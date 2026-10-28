"""Infra da suíte de ponta a ponta (Playwright + pytest).

Cada caso roda num contexto novo do navegador, e os bancos são restaurados
antes de cada um (ver `apoio.py`). Ao final, `resultados/` guarda um
screenshot e um vídeo por caso, e o `resultados.json` com o placar.
"""
import json
import os
import shutil
import time

import pytest
from playwright.sync_api import sync_playwright

from apoio import FRONT, RESULTADOS, AmbienteInvalido, conferir_ambiente, copiar_bancos

VISIVEL = os.getenv("E2E_VISIVEL") == "1"

VIEWPORTS = {
    "desktop": {"viewport": {"width": 1366, "height": 900}},
    "mobile": {"viewport": {"width": 390, "height": 844}, "is_mobile": True, "has_touch": True},
}


@pytest.fixture(scope="session")
def copia_dos_bancos():
    try:
        conferir_ambiente()
    except AmbienteInvalido as erro:
        pytest.exit(str(erro), returncode=2)
    restaurar = copiar_bancos()
    yield restaurar
    restaurar()


@pytest.fixture(autouse=True)
def banco_limpo(copia_dos_bancos):
    copia_dos_bancos()


@pytest.fixture(scope="session")
def navegador():
    with sync_playwright() as p:
        nav = p.chromium.launch(headless=not VISIVEL, slow_mo=150 if VISIVEL else 0)
        yield nav
        nav.close()


@pytest.fixture
def abrir(request, navegador):
    """Abre uma página num contexto novo, gravando vídeo.

    Aceita "desktop" ou "mobile". No fim do caso salva o screenshot da última
    página aberta e o vídeo dela com o código do caso no nome.
    """
    caso = request.node.name.split("_")[1].upper()
    abertos = []

    def _abrir(tamanho: str = "desktop"):
        pasta_video = RESULTADOS / "videos" / f"{caso}-{len(abertos)}"
        ctx = navegador.new_context(
            locale="pt-BR", record_video_dir=str(pasta_video),
            record_video_size=VIEWPORTS[tamanho]["viewport"], **VIEWPORTS[tamanho],
        )
        ctx.set_default_timeout(10_000)
        page = ctx.new_page()
        abertos.append((ctx, page, tamanho, pasta_video))
        return page

    yield _abrir

    (RESULTADOS / "screenshots").mkdir(parents=True, exist_ok=True)
    if abertos:
        _, ultima, tamanho, _ = abertos[-1]
        try:
            ultima.screenshot(path=str(RESULTADOS / "screenshots" / f"{caso}.png"))
        except Exception:
            pass
        request.node.user_properties.append(("viewport", tamanho))
    for indice, (ctx, page, _, pasta_video) in enumerate(abertos):
        video = page.video
        ctx.close()
        if video and indice == len(abertos) - 1:
            destino = RESULTADOS / "videos" / f"{caso}.webm"
            if destino.exists():
                destino.unlink()
            video.save_as(str(destino))
            request.node.user_properties.append(("video", destino.name))
        shutil.rmtree(pasta_video, ignore_errors=True)


_resultados = []
_inicio = time.time()


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        _resultados.append({
            "id": report.nodeid.split("::")[-1].split("_")[1].upper(),
            "teste": report.nodeid.split("::")[-1],
            "status": report.outcome,
            "duracao": round(report.duration, 2),
            "erro": str(report.longrepr.reprcrash.message)
            if report.failed and hasattr(report.longrepr, "reprcrash") else "",
        })
    elif report.when == "teardown" and _resultados:
        props = dict(report.user_properties)
        _resultados[-1].update({k: v for k, v in props.items() if k in ("video", "viewport")})


def pytest_sessionfinish(session):
    if not _resultados:
        return
    RESULTADOS.mkdir(exist_ok=True)
    with open(RESULTADOS / "resultados.json", "w", encoding="utf-8") as f:
        json.dump({
            "data": time.strftime("%d/%m/%Y %H:%M"),
            "duracao_total": round(time.time() - _inicio, 1),
            "frontend": FRONT,
            "casos": _resultados,
        }, f, ensure_ascii=False, indent=1)

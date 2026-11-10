"""Gateway: o /health consulta os serviços em paralelo e o cliente
compartilhado não carrega cookie de um usuário para outro."""
import asyncio
import time

import httpx

from conftest import carregar

config, proxy = carregar("gateway", "config", "proxy")

ATRASO = 0.3


def registro():
    return config.ServiceRegistry({
        nome: {"url": f"http://{nome}.teste", "porta": 8000 + i, "descricao": ""}
        for i, nome in enumerate(
            ["imoveis", "usuarios", "contratos", "notificacoes", "recomendacao", "agente"],
            start=1,
        )
    })


def test_agente_tem_prazo_maior_que_os_outros_servicos():
    """O modelo pode levar mais de 10 s; com o prazo padrao o gateway desistia
    da pergunta e devolvia 502."""
    registro = config.ServiceRegistry(config.SERVICES)
    assert registro.timeout("agente", 10.0) == 120.0
    assert registro.timeout("imoveis", 10.0) == 10.0


def cliente_com(handler):
    return proxy.novo_cliente_http(httpx.MockTransport(handler))


async def servico_lento(request):
    await asyncio.sleep(ATRASO)
    if request.url.host == "agente.teste":
        raise httpx.ConnectError("recusada", request=request)
    return httpx.Response(200, json={"status": "ok"})


def test_health_consulta_os_servicos_em_paralelo():
    monitor = proxy.MonitorServicos(registro(), cliente_com(servico_lento))

    inicio = time.perf_counter()
    estado = asyncio.run(monitor.verificar())
    decorrido = time.perf_counter() - inicio

    assert decorrido < ATRASO * 3, f"levou {decorrido:.2f}s; em série seriam {ATRASO * 6:.1f}s"
    assert estado["servicos"]["agente"]["status"] == "indisponivel"
    assert estado["servicos"]["imoveis"] == {"status": "ok", "porta": 8001}
    assert estado["status_geral"] == "degradado"


def test_cliente_compartilhado_nao_guarda_cookie():
    def define_cookie(request):
        return httpx.Response(200, headers={"set-cookie": "sessao=da-ana; Path=/"})

    cliente = cliente_com(define_cookie)

    async def duas_requisicoes():
        await cliente.get("http://usuarios.teste/qualquer")
        return await cliente.get("http://usuarios.teste/outra")

    segunda = asyncio.run(duas_requisicoes())
    assert "cookie" not in segunda.request.headers
    assert not cliente.cookies

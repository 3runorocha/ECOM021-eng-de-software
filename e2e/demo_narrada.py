"""Grava a demonstração narrada do sistema, do gateway aos três perfis.

    python demo_narrada.py              # grava sem abrir janela
    python demo_narrada.py --visivel    # mostra o navegador enquanto grava
    python demo_narrada.py --roteiro    # só escreve o roteiro em .md

Como a fala fica sincronizada com a imagem:
  1. cada passo tem uma frase; o edge-tts gera um áudio por frase;
  2. a duração de cada áudio é medida com o ffprobe;
  3. na gravação, cada passo espera a própria fala terminar antes de seguir,
     e o instante em que ele começou fica anotado;
  4. o ffmpeg posiciona cada áudio no instante do seu passo e junta tudo ao
     vídeo num MP4 (H.264 + AAC).

Precisa de internet (o edge-tts usa o serviço de voz da Microsoft) e do
ffmpeg no PATH. Os bancos são restaurados no fim.
"""
import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import time

import edge_tts
from playwright.sync_api import sync_playwright

from apoio import FRONT, GATEWAY, RESULTADOS, conferir_ambiente, copiar_bancos, entrar

VOZ = "pt-BR-FranciscaNeural"
TELA = {"width": 1366, "height": 900}
PAUSA = 1.2
DIGITACAO = 70
PASTA = RESULTADOS / "demo"

CURSOR = """
window.addEventListener('DOMContentLoaded', () => {
  const c = document.createElement('div');
  c.style.cssText = 'position:fixed;z-index:2147483647;pointer-events:none;width:18px;height:18px;'
    + 'border-radius:50%;background:rgba(37,99,235,.35);border:2px solid #2563eb;'
    + 'left:-40px;top:-40px;transform:translate(-50%,-50%);transition:left .25s,top .25s';
  document.body.appendChild(c);
  document.addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; });
  document.addEventListener('mousedown', () => c.style.background = 'rgba(37,99,235,.8)');
  document.addEventListener('mouseup', () => c.style.background = 'rgba(37,99,235,.35)');
});
"""

FORMATAR_JSON = """() => {
  const dados = JSON.parse(document.body.innerText);
  const pre = document.createElement('pre');
  pre.textContent = JSON.stringify(dados, null, 2);
  pre.style.cssText = 'font-size:19px;line-height:1.45;margin:28px 64px;font-family:Consolas,monospace';
  document.body.replaceChildren(pre);
}"""

DESTACAR_INVALIDOS ="form input:invalid { outline: 2px solid #dc2626 !important; background: #fef2f2 !important; }"


def menu(page, rota):
    page.click(f"aside a[href='{rota}']")
    page.wait_for_load_state("networkidle")


def digitar(page, seletor, texto):
    campo = page.locator(seletor)
    campo.click()
    campo.fill("")
    campo.press_sequentially(texto, delay=DIGITACAO)


def apontar(page, alvo):
    page.locator(alvo).first.hover()


def contagem(page, texto):
    page.locator(f"text='{texto}'").wait_for()


def rolar(page, pixels, passos=6):
    for _ in range(passos):
        page.mouse.wheel(0, pixels / passos)
        page.wait_for_timeout(120)


def p01(page):
    page.goto(GATEWAY + "/health")
    page.evaluate(FORMATAR_JSON)
    page.wait_for_timeout(500)


def p02(page):
    for servico in ("imoveis", "usuarios", "contratos", "notificacoes", "recomendacao", "agente"):
        page.locator(f"text=/\"{servico}\"/").first.hover()
        page.wait_for_timeout(700)


def p03(page):
    page.goto(GATEWAY + "/docs")
    page.locator(".opblock").first.wait_for()
    page.mouse.move(683, 450)
    rolar(page, 900, 10)


def p04(page):
    page.goto(FRONT + "/")
    page.locator("input[type=email]").press_sequentially("admin@alugue.br", delay=DIGITACAO)
    page.locator("input[type=password]").press_sequentially("errada", delay=DIGITACAO)
    page.click("button[type=submit]")
    page.locator("text=Email ou senha inválidos").wait_for()


def p05(page):
    campo = page.locator("input[type=password]")
    campo.fill("")
    campo.press_sequentially("admin123", delay=DIGITACAO)
    page.click("button[type=submit]")
    page.locator("text=Sair").wait_for()


def p06(page):
    page.locator("text=9 disponíveis").wait_for()
    apontar(page, "text=9 disponíveis")


def p07(page):
    apontar(page, "text=3 em atraso")
    page.wait_for_timeout(1500)
    apontar(page, "text=R$ 30.480")


def p08(page):
    apontar(page, "text=Gateway - :8000")
    page.mouse.move(120, 760, steps=25)


def p09(page):
    menu(page, "/imoveis")
    contagem(page, "18 imóvel(is)")
    rolar(page, 400)
    rolar(page, -400)


def p10(page):
    digitar(page, "input[placeholder^='Buscar']", "Boa Viagem")
    contagem(page, "2 imóvel(is)")


def p11(page):
    digitar(page, "input[placeholder^='Buscar']", "Pituba")
    page.locator("text=Nenhum imóvel para esses filtros.").wait_for()


def p12(page):
    page.locator("input[placeholder^='Buscar']").fill("")
    digitar(page, "input[placeholder='qualquer']", "Maceió")
    contagem(page, "8 imóvel(is)")


def p13(page):
    digitar(page, "input[placeholder='qualquer']", "maceio")
    contagem(page, "8 imóvel(is)")


def p14(page):
    page.locator("main select").nth(0).select_option("casa")
    contagem(page, "2 imóvel(is)")


def p15(page):
    page.locator("main select").nth(2).select_option("true")
    contagem(page, "1 imóvel(is)")
    digitar(page, "input[placeholder='sem limite']", "2000")
    apontar(page, "text=Casa no Tabuleiro")


def p16(page):
    page.click("text=Limpar")
    contagem(page, "18 imóvel(is)")


def p17(page):
    page.click("text=+ Novo imóvel")
    page.add_style_tag(content=DESTACAR_INVALIDOS)
    page.locator("form button[type=submit]").click()


def p18(page):
    form = page.locator("form")
    form.locator("select").select_option("casa")
    textos = form.locator("input[type=text]")
    for indice, valor in enumerate(["Casa Nova na Ponta Verde", "Rua das Acácias, 120", "Maceió"]):
        textos.nth(indice).press_sequentially(valor, delay=DIGITACAO)
    numeros = form.locator("input[type=number]")
    for indice, valor in enumerate(["3", "2", "140", "2800"]):
        numeros.nth(indice).press_sequentially(valor, delay=DIGITACAO)


def p19(page):
    page.locator("form button[type=submit]").click()
    contagem(page, "19 imóvel(is)")
    novo = page.locator("text='Casa Nova na Ponta Verde'")
    novo.scroll_into_view_if_needed()
    novo.hover()


def p20(page):
    menu(page, "/contratos")
    page.locator("tbody tr").first.wait_for()
    rolar(page, 300)
    rolar(page, -300)


def p21(page):
    page.locator("main select").first.select_option("atrasado")
    page.locator("text=/venceu há/").first.wait_for()
    apontar(page, "text=/venceu há/")


def p22(page):
    page.locator("main select").first.select_option("")
    page.click("text=+ Novo contrato")
    apontar(page, "text=/Imóvel disponível/")


def p23(page):
    form = page.locator("form")
    form.locator("select").nth(0).select_option(label="Ana Souza")
    page.wait_for_timeout(600)
    valor = form.locator("option", has_text="Apartamento no Serraria").get_attribute("value")
    form.locator("select").nth(1).select_option(valor)
    page.wait_for_timeout(600)
    form.locator("button[type=submit]").click()


def p24(page):
    ativa = page.locator("tbody tr", has_text="Apartamento no Serraria").filter(has_text="Ativo")
    ativa.wait_for()
    ativa.hover()
    page.wait_for_timeout(1500)
    page.click("text=+ Novo contrato")
    apontar(page, "text=/Imóvel disponível/")


def p25(page):
    page.locator("form >> text=Cancelar").click()
    linha = page.locator("tbody tr", has_text="Apartamento no Serraria").filter(has_text="Ativo")
    numero = linha.locator("td").first.inner_text().strip()
    linha.locator("text=Encerrar").click()
    alvo = page.locator("tbody tr", has=page.locator(f"td:text-is('{numero}')"))
    alvo.filter(has_text="Encerrado").wait_for()
    alvo.hover()


def p26(page):
    menu(page, "/imoveis")
    digitar(page, "input[placeholder^='Buscar']", "Serraria")
    contagem(page, "1 imóvel(is)")
    apontar(page, "main >> text='Disponível'")


def p27(page):
    menu(page, "/usuarios")
    page.locator("tbody tr").first.wait_for()
    apontar(page, "text=CONTRATOS EM VIGOR")


def p28(page):
    linha = page.locator("tr", has_text="joao@alugue.br")
    linha.hover()
    page.wait_for_timeout(800)
    linha.locator("select").select_option("proprietario")
    page.wait_for_timeout(800)


def p29(page):
    menu(page, "/notificacoes")
    page.click("text=Rodar varredura")
    page.locator("text=1 não lida(s) de 1").wait_for()
    apontar(page, "text=/venceu há/")


def p30(page):
    page.click("text=Marcar lida")
    page.locator("text=0 não lida(s) de 1").wait_for()
    apontar(page, "text=0 não lida(s) de 1")


def p31(page):
    menu(page, "/recomendacao")
    page.locator("main select").first.select_option(label="Ana Souza")
    page.click("text=Recomendar imóveis")
    page.locator("text=Perfil calculado").wait_for()
    apontar(page, "text=Perfil calculado")


def p32(page):
    apontar(page, "text=/está entre seus preferidos/")
    rolar(page, 350)


def p33(page):
    menu(page, "/agente")
    apontar(page, "text=Agente sem credencial")


def p34(page):
    digitar(page, "input[placeholder='O que você procura?']", "casa em Maceió até 3 mil reais")
    page.click("main button[type=submit]")
    page.locator("text=/Defina ANTHROPIC_API_KEY no ambiente/").wait_for()


def p35(page):
    page.click("text=Sair")
    entrar(page, "beatriz", atraso=DIGITACAO)


def p36(page):
    menu(page, "/imoveis")
    apontar(page, "text=+ Novo imóvel")


def p37(page):
    menu(page, "/usuarios")
    apontar(page, "text=beatriz@alugue.br")


def p38(page):
    page.click("text=Sair")
    entrar(page, "ana", atraso=DIGITACAO)


def p39(page):
    menu(page, "/imoveis")
    contagem(page, "19 imóvel(is)")
    page.mouse.move(1150, 70, steps=15)


def p40(page):
    menu(page, "/contratos")
    page.locator("tbody tr").first.wait_for()
    apontar(page, "text=INQUILINO")


def p41(page):
    menu(page, "/")
    page.locator("text='Contratos em vigor'").wait_for()


PASSOS = [
    ("Abertura e arquitetura", p01, "Este é o sistema de aluguel de imóveis, desenvolvido para a disciplina de Engenharia de Software. Começamos pela arquitetura, consultando a saúde do sistema pelo gateway."),
    ("Abertura e arquitetura", p02, "O gateway responde por sete processos: ele mesmo e seis microsserviços independentes, de imóveis, usuários, contratos, notificações, recomendação e o agente de inteligência artificial. Cada um tem o próprio banco de dados."),
    ("Abertura e arquitetura", p03, "Esta é a documentação da API do gateway. Toda requisição externa passa por aqui: o gateway valida o token e encaminha a chamada ao microsserviço responsável."),
    ("Acesso e painel", p04, "Agora, a interface web. Se a senha estiver errada, o acesso é recusado com uma mensagem clara."),
    ("Acesso e painel", p05, "Com as credenciais corretas, entramos como administrador."),
    ("Acesso e painel", p06, "O painel reúne números reais, consultados nos serviços: dezoito imóveis no portfólio, nove deles disponíveis, e nove contratos em vigor."),
    ("Acesso e painel", p07, "Três contratos estão em atraso, e a receita mensal contratada soma trinta mil, quatrocentos e oitenta reais."),
    ("Acesso e painel", p08, "No menu lateral, o status de cada serviço é verificado em tempo real. Se algum cair, o indicador muda, e as telas mostram o erro em vez de dados inventados."),
    ("Catálogo de imóveis", p09, "Na tela de imóveis está o portfólio completo, com tipo, cidade, quartos, valor do aluguel e situação."),
    ("Catálogo de imóveis", p10, "A busca procura no título e no endereço. Ao digitar Boa Viagem, restam dois imóveis."),
    ("Catálogo de imóveis", p11, "Quando nada corresponde, a tela informa que não há imóveis para esses filtros, em vez de ficar simplesmente vazia."),
    ("Catálogo de imóveis", p12, "O filtro de cidade é aplicado no próprio serviço de imóveis. Digitando Maceió, com acento, aparecem oito imóveis."),
    ("Catálogo de imóveis", p13, "Sem acento e em letras minúsculas, o resultado é o mesmo: o serviço compara os nomes ignorando acentos e maiúsculas."),
    ("Catálogo de imóveis", p14, "Os filtros se combinam. Restringindo a casas, ficam duas opções em Maceió."),
    ("Catálogo de imóveis", p15, "Somando a situação disponível e o aluguel de até dois mil reais, sobra uma única casa: a Casa no Tabuleiro."),
    ("Catálogo de imóveis", p16, "O botão Limpar desfaz todos os filtros, e o catálogo volta aos dezoito imóveis."),
    ("Catálogo de imóveis", p17, "O administrador pode cadastrar imóveis. O formulário não aceita campos obrigatórios em branco."),
    ("Catálogo de imóveis", p18, "Preenchemos os dados de uma nova casa em Maceió: título, endereço, quartos, banheiros, área e valor do aluguel."),
    ("Catálogo de imóveis", p19, "Ao salvar, o imóvel entra no portfólio já como disponível, e o catálogo passa a ter dezenove imóveis."),
    ("Contratos", p20, "Na tela de contratos, o administrador vê todos os aluguéis, com datas, valor e situação."),
    ("Contratos", p21, "Filtrando os atrasados, cada contrato mostra há quantos dias venceu. A multa é proporcional ao aluguel: um trinta avos do valor mensal por dia de atraso."),
    ("Contratos", p22, "Vamos registrar um novo aluguel. O formulário oferece apenas imóveis sem contrato em aberto."),
    ("Contratos", p23, "Escolhemos a inquilina Ana e o Apartamento no Serraria. O prazo padrão é de doze meses, contados a partir de hoje."),
    ("Contratos", p24, "O contrato entra como ativo, e o imóvel sai da lista de disponíveis. Um imóvel só aceita um contrato aberto por vez, e essa regra é garantida no serviço e também no banco de dados."),
    ("Contratos", p25, "Ao encerrar o contrato, a data de término real é registrada. Como a devolução foi dentro do prazo, não há multa."),
    ("Contratos", p26, "De volta ao catálogo, o Apartamento no Serraria está novamente disponível para um novo aluguel."),
    ("Usuários, notificações, recomendação e agente", p27, "Na gestão de usuários, o administrador vê cada pessoa, o perfil dela e quantos contratos tem em vigor."),
    ("Usuários, notificações, recomendação e agente", p28, "O cadastro público cria apenas inquilinos. Para alguém administrar imóveis, o administrador o promove a proprietário, como fazemos agora com João."),
    ("Usuários, notificações, recomendação e agente", p29, "O serviço de notificações varre os contratos e gera alertas. Executando a varredura, surge um aviso de atraso com a multa acumulada."),
    ("Usuários, notificações, recomendação e agente", p30, "Ao marcar o alerta como lido, o contador de não lidas é atualizado."),
    ("Usuários, notificações, recomendação e agente", p31, "O serviço de recomendação monta o perfil de cada inquilino a partir do histórico de contratos, identificando os tipos de imóvel e as cidades que ele mais alugou."),
    ("Usuários, notificações, recomendação e agente", p32, "Com esse perfil, os imóveis disponíveis recebem uma pontuação, e cada sugestão explica o motivo."),
    ("Usuários, notificações, recomendação e agente", p33, "A tela do agente aceita perguntas em linguagem natural. Ele usa a API do Claude e consulta o sistema pelos mesmos componentes que as outras aplicações usam."),
    ("Usuários, notificações, recomendação e agente", p34, "Sem a chave da API configurada, o agente avisa com clareza o que falta, e o restante do sistema continua funcionando normalmente."),
    ("Perfis e fechamento", p35, "Agora, os outros perfis. Beatriz é proprietária."),
    ("Perfis e fechamento", p36, "Como proprietária, ela pode cadastrar e administrar imóveis."),
    ("Perfis e fechamento", p37, "Na lista de usuários, ela apenas consulta: só o administrador muda perfis."),
    ("Perfis e fechamento", p38, "Por fim, a inquilina Ana."),
    ("Perfis e fechamento", p39, "Ela consulta o catálogo, mas não tem a opção de cadastrar imóveis. Se tentasse pela API, o serviço recusaria com erro de permissão."),
    ("Perfis e fechamento", p40, "Na tela de contratos, ela vê somente os próprios aluguéis, e só pode registrar contratos em seu próprio nome."),
    ("Perfis e fechamento", p41, "Em resumo: microsserviços independentes atrás de um gateway, regras de negócio garantidas no backend, e um agente de inteligência artificial integrado como mais um componente. Obrigado pela atenção."),
]


def escrever_roteiro() -> None:
    linhas = ["# Roteiro da narração", "", f"Voz: {VOZ} (edge-tts). Uma frase por passo.", ""]
    secao = None
    for numero, (titulo, _, fala) in enumerate(PASSOS, 1):
        if titulo != secao:
            linhas += ["", f"## {titulo}", ""]
            secao = titulo
        linhas.append(f"{numero}. {fala}")
    PASTA.mkdir(parents=True, exist_ok=True)
    (PASTA / "roteiro_narracao.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


async def _gerar_audios(pasta) -> None:
    limite = asyncio.Semaphore(4)

    async def um(numero, fala):
        async with limite:
            await edge_tts.Communicate(fala, VOZ).save(str(pasta / f"{numero:02d}.mp3"))

    await asyncio.gather(*(um(n, fala) for n, (_, _, fala) in enumerate(PASSOS, 1)))


def duracao(arquivo) -> float:
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arquivo)],
        capture_output=True, text=True, check=True)
    return float(saida.stdout.strip())


def abrir_navegador(p, visivel):
    """Prefere o Edge, que já vem no Windows e mostra as mensagens do navegador
    (como "Preencha este campo.") em português. Sem ele, usa o Chromium do
    Playwright, que as mostra em inglês."""
    opcoes = {"headless": not visivel, "slow_mo": 350, "args": ["--lang=pt-BR"]}
    try:
        return p.chromium.launch(channel="msedge", **opcoes)
    except Exception:
        return p.chromium.launch(**opcoes)


def gravar(duracoes, visivel) -> tuple:
    marcas = []
    with sync_playwright() as p:
        nav = abrir_navegador(p, visivel)
        ctx = nav.new_context(viewport=TELA, record_video_dir=str(PASTA / "bruto"),
                              record_video_size=TELA, locale="pt-BR")
        ctx.add_init_script(CURSOR)
        ctx.set_default_timeout(20_000)
        page = ctx.new_page()
        zero = time.monotonic()
        page.wait_for_timeout(800)
        for numero, ((_, acao, _), fala) in enumerate(zip(PASSOS, duracoes), 1):
            inicio = time.monotonic() - zero
            marcas.append(inicio)
            acao(page)
            restante = inicio + fala + PAUSA - (time.monotonic() - zero)
            if restante > 0:
                page.wait_for_timeout(restante * 1000)
            print(f"  passo {numero:02d} em {inicio:6.1f}s  (fala {fala:4.1f}s)")
        page.wait_for_timeout(1500)
        video = page.video
        ctx.close()
        bruto = PASTA / "video_sem_audio.webm"
        video.save_as(str(bruto))
        video.delete()
        nav.close()
    return bruto, marcas


def juntar(bruto, marcas, audios) -> None:
    entradas = ["-i", str(bruto)]
    filtros = []
    for indice, (audio, marca) in enumerate(zip(audios, marcas), 1):
        entradas += ["-i", str(audio)]
        atraso = int(marca * 1000)
        filtros.append(f"[{indice}:a]adelay={atraso}|{atraso}[a{indice}]")
    mistura = "".join(f"[a{i}]" for i in range(1, len(audios) + 1))
    filtros.append(f"{mistura}amix=inputs={len(audios)}:normalize=0[voz]")
    final = PASTA / "demonstracao_narrada.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *entradas, "-filter_complex", ";".join(filtros),
         "-map", "0:v", "-map", "[voz]", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(final)],
        check=True)
    print(f"Vídeo final: {final}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--visivel", action="store_true", help="mostra o navegador durante a gravação")
    parser.add_argument("--roteiro", action="store_true", help="só escreve o roteiro em .md")
    args = parser.parse_args()

    escrever_roteiro()
    if args.roteiro:
        print(f"Roteiro em {PASTA / 'roteiro_narracao.md'}")
        return 0
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("ffmpeg/ffprobe não encontrados no PATH; veja o README desta pasta.")
        return 1
    conferir_ambiente()

    pasta_audio = PASTA / "audio"
    pasta_audio.mkdir(parents=True, exist_ok=True)
    print(f"Gerando {len(PASSOS)} falas com {VOZ}...")
    asyncio.run(_gerar_audios(pasta_audio))
    audios = [pasta_audio / f"{n:02d}.mp3" for n in range(1, len(PASSOS) + 1)]
    duracoes = [duracao(a) for a in audios]
    print(f"Narração: {sum(duracoes) / 60:.1f} min de fala")

    restaurar = copiar_bancos()
    try:
        print("Gravando...")
        bruto, marcas = gravar(duracoes, args.visivel)
    finally:
        restaurar()

    (PASTA / "marcas.json").write_text(json.dumps(
        [{"passo": n, "inicio": round(m, 2), "fala": round(d, 2), "texto": t}
         for n, (m, d, (_, _, t)) in enumerate(zip(marcas, duracoes, PASSOS), 1)],
        ensure_ascii=False, indent=1), encoding="utf-8")
    juntar(bruto, marcas, audios)
    return 0


if __name__ == "__main__":
    sys.exit(main())

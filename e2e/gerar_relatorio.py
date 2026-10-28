"""Monta o relatório HTML da suíte a partir de `resultados/`.

    python gerar_relatorio.py

Lê o `resultados.json` da última execução, os cenários de `casos.feature`,
os screenshots e vídeos de cada caso e o vídeo narrado, e escreve
`resultados/relatorio/index.html` com as mídias ao lado.
"""
import html
import json
import re
import shutil
import subprocess

from apoio import FRONT, RAIZ, RESULTADOS

SAIDA = RESULTADOS / "relatorio"
NAVEGADOR = "Chromium 156 (Playwright, sem janela)"

ACHADOS = [
    ("Defeito", "CT26", "A recomendação não confere quem está pedindo",
     "Logada como inquilina, a Ana abre a tela de recomendação já no usuário Admin e pode "
     "escolher qualquer um dos 7 usuários. O serviço de recomendação responde para qualquer id, "
     "então o perfil (tipos e cidades que a pessoa alugou) de outros usuários fica exposto.",
     "Usar no serviço a identidade repassada pelo gateway, como contratos e imóveis já fazem, "
     "e abrir a tela no próprio usuário."),
    ("Defeito", "CT29", "No celular, o menu lateral espreme o conteúdo",
     "Em 390 px o menu fica fixo com 220 px e a área de conteúdo com 170 px. A página não rola "
     "na horizontal, mas a tabela de contratos e o botão \"+ Novo contrato\" ficam cortados.",
     "Abaixo de 768 px, recolher o menu atrás de um botão e dar a largura toda ao conteúdo."),
    ("Observação", "CT19", "Encerrar contrato não pede confirmação",
     "Um clique em \"Encerrar\" grava a data de término na hora, sem confirmação e sem como "
     "desfazer pela tela.", "Pedir confirmação mostrando a multa que será cobrada."),
    ("Observação", "CT22", "Mudar o perfil de alguém não pede confirmação",
     "Trocar o perfil no seletor grava a mudança na hora, inclusive para admin.",
     "Confirmar antes de gravar, ao menos ao promover alguém a admin."),
    ("Observação", "CT24", "Multa da notificação sem formato de moeda",
     "O alerta mostra \"Multa acumulada: R$ 10573.33.\", enquanto o resto do sistema escreve "
     "\"R$ 10.573,33\".", "Formatar o valor em reais no texto da notificação."),
    ("Observação", "CT23", "Qualquer perfil vê nome e e-mail de todos os usuários",
     "A inquilina abre a tela de usuários e vê a lista completa, com os e-mails.",
     "Restringir a lista ao admin, ou esconder os e-mails para os outros perfis."),
    ("Observação", "CT24", "Qualquer perfil pode rodar a varredura de notificações",
     "O botão \"Rodar varredura\" aparece para a inquilina e varre os contratos de todos.",
     "Mostrar o botão só para o admin."),
    ("Melhoria", "CT12", "Filtro de aluguel aceita valor negativo",
     "\"Aluguel até\" aceita -5 e a lista fica vazia, sem dizer por quê.",
     "Limitar o campo a zero ou mais."),
    ("Melhoria", "CT27", "Botão Perguntar ativo mesmo sem credencial",
     "Com o aviso \"Agente sem credencial\" na tela, o botão continua habilitado e a pergunta "
     "volta com a mesma explicação.", "Desabilitar o campo e o botão enquanto o agente estiver sem chave."),
]

DENTRO = [
    "Login, sessão, saída e rotas protegidas",
    "Menu lateral e painel com os números reais",
    "Catálogo: busca, filtros combinados, estado vazio e cadastro com validação",
    "Contratos: assinar, encerrar, filtro de status e regra de um contrato por imóvel",
    "Permissões dos perfis admin, proprietária e inquilina",
    "Usuários, notificações, recomendação e o aviso do agente sem credencial",
    "Celular em 390 px",
]
FORA = [
    "Qualidade das respostas do agente de IA: não há chave da API neste ambiente",
    "Cadastro público de usuário: existe só pela API, sem tela",
    "Upload de arquivos: o sistema não tem",
    "Chamadas diretas às APIs, já cobertas pelos testes de unidade e de integração do projeto",
    "Firefox e Safari, carga e desempenho, e auditoria de acessibilidade",
]
ABORDAGEM = [
    "Exploração com Playwright nos três perfis e em dois tamanhos de tela antes de escrever os casos.",
    "Casos em Gherkin (casos.feature), um teste pytest para cada um, com o mesmo código CT.",
    "Cada caso roda num contexto novo do navegador, e os bancos são restaurados antes de cada um.",
    "Vídeo e screenshot ao final de cada caso. Falha de seletor foi corrigida no teste; falha de comportamento virou achado.",
]

PASSOS = [
    ("Instale o Python", "Baixe em python.org/downloads. Na primeira tela do instalador, marque "
     "<b>Add Python to PATH</b> antes de clicar em Install Now."),
    ("Abra o terminal na pasta", "No Explorador de Arquivos, abra a pasta <code>e2e</code>, clique "
     "na barra de endereço, digite <code>powershell</code> e aperte Enter."),
    ("Instale as ferramentas", None),
    ("Deixe o sistema no ar", "Os serviços (<code>python subir_servicos.py</code>) e o frontend "
     "(<code>npm run dev</code>) precisam estar rodando, com os dados de exemplo do "
     "<code>seed.py</code> e do <code>seed_contratos.py</code>."),
    ("Rode os testes", None),
    ("Rode um caso só", None),
    ("Grave a demonstração narrada", "Precisa do ffmpeg: baixe o build \"release full\" em "
     "gyan.dev/ffmpeg/builds, extraia, adicione a pasta <code>bin</code> à variável PATH do "
     "Windows e confira com <code>ffmpeg -version</code>."),
]
COMANDOS = {
    "Instale as ferramentas": ["pip install playwright pytest edge-tts httpx",
                               "python -m playwright install chromium"],
    "Rode os testes": ["python -m pytest test_prototipo.py -v"],
    "Rode um caso só": ["python -m pytest test_prototipo.py -v -k CT14"],
    "Grave a demonstração narrada": ["python demo_narrada.py --visivel"],
}


def ler_cenarios():
    modulos, cenarios, atual, modulo = [], {}, None, None
    for linha in (RAIZ / "casos.feature").read_text(encoding="utf-8").splitlines():
        texto = linha.strip()
        if texto.startswith("Funcionalidade:"):
            modulo = texto.split(":", 1)[1].strip()
            modulos.append(modulo)
            atual = None
        elif texto.startswith("Cenário:"):
            codigo, titulo = texto.split(":", 1)[1].strip().split(" ", 1)
            atual = {"modulo": modulo, "titulo": titulo, "linhas": [f"Cenário: {codigo} {titulo}"]}
            cenarios[codigo] = atual
        elif atual and texto:
            atual["linhas"].append("  " + texto)
    return modulos, cenarios


def gherkin(linhas):
    saida = []
    for linha in linhas:
        seguro = html.escape(linha)
        seguro = re.sub(r"^(\s*)(Cenário:|Dado|Quando|Então|E)\b", r'\1<b class="kw">\2</b>', seguro)
        seguro = re.sub(r"&quot;(.*?)&quot;", r'<span class="str">"\1"</span>', seguro)
        saida.append(seguro)
    return "\n".join(saida)


def status_html(status):
    if status == "passed":
        return '<span class="etiqueta verde">Aprovado</span>'
    return '<span class="etiqueta vermelho">Falhou</span>'


COR_DO_TIPO = {"Defeito": "vermelho", "Observação": "laranja", "Melhoria": "amarelo"}


def montar():
    dados = json.loads((RESULTADOS / "resultados.json").read_text(encoding="utf-8"))
    casos = {c["id"]: c for c in dados["casos"]}
    modulos, cenarios = ler_cenarios()
    aprovados = sum(c["status"] == "passed" for c in casos.values())
    total = len(casos)
    defeito_do_caso = {a[1]: a for a in ACHADOS if a[0] == "Defeito"}
    contagem = {t: sum(a[0] == t for a in ACHADOS) for t in ("Defeito", "Observação", "Melhoria")}

    tabelas = []
    for modulo in modulos:
        linhas = []
        for codigo, cen in cenarios.items():
            if cen["modulo"] != modulo or codigo not in casos:
                continue
            c = casos[codigo]
            nota = ""
            if codigo in defeito_do_caso:
                nota = f'<span class="nota">Defeito: {html.escape(defeito_do_caso[codigo][2])}</span>'
            linhas.append(
                f'<tr><td class="mono"><a href="#{codigo.lower()}">{codigo}</a></td>'
                f'<td>{html.escape(cen["titulo"])}{nota}</td>'
                f'<td>{status_html(c["status"])}</td>'
                f'<td class="mono num">{c["duracao"]:.1f} s</td></tr>')
        aprovados_modulo = sum(
            casos[k]["status"] == "passed" for k, v in cenarios.items() if v["modulo"] == modulo and k in casos)
        total_modulo = sum(1 for k, v in cenarios.items() if v["modulo"] == modulo and k in casos)
        tabelas.append(
            f'<article class="card"><div class="card-topo"><h3>{html.escape(modulo)}</h3>'
            f'<span class="card-meta">{aprovados_modulo}/{total_modulo} aprovados</span></div>'
            f'<div class="tabela"><table><thead><tr><th>ID</th><th>Cenário</th><th>Status</th>'
            f'<th class="num">Duração</th></tr></thead><tbody>{"".join(linhas)}</tbody></table></div></article>')

    itens_achados = []
    for numero, (tipo, caso, titulo, detalhe, sugestao) in enumerate(ACHADOS, 1):
        itens_achados.append(
            f'<article class="card"><div class="card-topo">'
            f'<span class="etiqueta {COR_DO_TIPO[tipo]}">{tipo}</span>'
            f'<span class="card-meta">A{numero:02d} · <a href="#{caso.lower()}">{caso}</a></span></div>'
            f'<h3>{html.escape(titulo)}</h3><p>{html.escape(detalhe)}</p>'
            f'<p class="sugestao"><b>Sugestão:</b> {html.escape(sugestao)}</p>'
            f'<div class="card-acoes"><a class="botao botao-primario" href="#{caso.lower()}">Abrir o caso {caso}</a>'
            f'<a class="botao" href="#resultados">Ver os resultados</a></div></article>')

    detalhes = []
    for codigo, cen in cenarios.items():
        c = casos.get(codigo)
        if not c:
            continue
        erro = ""
        if c["status"] != "passed":
            erro = f'<pre class="erro">{html.escape(c["erro"].splitlines()[0])}</pre>'
        video = ""
        if c.get("video"):
            video = (f'<video controls preload="none" poster="screenshots/{codigo}.png" '
                     f'src="videos/{c["video"]}"></video><p class="legenda">Vídeo da execução do caso.</p>')
        detalhes.append(
            f'<details class="card caso" id="{codigo.lower()}"><summary>'
            f'<span class="mono codigo">{codigo}</span>'
            f'<span class="sum-titulo">{html.escape(cen["titulo"])}</span>{status_html(c["status"])}</summary>'
            f'<div class="caso-corpo"><p class="card-meta">{html.escape(cen["modulo"])} · '
            f'{c.get("viewport", "desktop")} · {c["duracao"]:.1f} s</p>'
            f'<pre class="gherkin">{gherkin(cen["linhas"])}</pre>{erro}'
            f'<img loading="lazy" src="screenshots/{codigo}.png" alt="Tela ao final do {codigo}">'
            f'<p class="legenda">Tela ao final do caso.</p>{video}</div></details>')

    passos = []
    for numero, (titulo, texto) in enumerate(PASSOS, 1):
        corpo = f"<p>{texto}</p>" if texto else ""
        for comando in COMANDOS.get(titulo, []):
            corpo += (f'<div class="cmd"><code>{html.escape(comando)}</code>'
                      f'<button type="button" class="botao copiar" data-cmd="{html.escape(comando)}">Copiar</button></div>')
        passos.append(f'<li><span class="passo-num">{numero}</span><div><h3>{titulo}</h3>{corpo}</div></li>')

    lista = lambda itens: "".join(f"<li>{html.escape(i)}</li>" for i in itens)
    pagina = MODELO.format(
        aprovados=aprovados, total=total, falhas=total - aprovados,
        data=dados["data"], url=html.escape(FRONT), navegador=NAVEGADOR,
        tempo=f'{dados["duracao_total"]:.0f} s',
        defeitos=contagem["Defeito"], observacoes=contagem["Observação"], melhorias=contagem["Melhoria"],
        dentro=lista(DENTRO), fora=lista(FORA), abordagem=lista(ABORDAGEM),
        tabelas="".join(tabelas), achados="".join(itens_achados),
        detalhes="".join(detalhes), passos="".join(passos),
        porcento=round(100 * aprovados / total),
    )
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "index.html").write_text(pagina, encoding="utf-8")


def copiar_midias():
    for pasta in ("screenshots", "videos"):
        destino = SAIDA / pasta
        destino.mkdir(parents=True, exist_ok=True)
        for arquivo in (RESULTADOS / pasta).iterdir():
            if arquivo.is_file():
                shutil.copy2(arquivo, destino / arquivo.name)
    demo = RESULTADOS / "demo" / "demonstracao_narrada.mp4"
    if demo.exists():
        shutil.copy2(demo, SAIDA / demo.name)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "62", "-i", str(demo),
                        "-frames:v", "1", "-q:v", "4", str(SAIDA / "capa.jpg")], check=False)


MODELO = """<title>Testes do Aluguel de Imóveis</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {{
  --fundo: #faf7f2; --superficie: #f1ece3; --borda: #ddd5c6;
  --tinta: #111; --tinta-suave: #4a4a4a; --marca: #e8112d;
  --vermelho: #e8112d; --laranja: #ff6b1a; --amarelo: #f5c400; --verde: #0fa958; --cinza: #5f6672;
  --codigo: #e9e2d6;
  --fonte-display: "Archivo Black", system-ui, sans-serif;
  --fonte-texto: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --fonte-mono: "JetBrains Mono", ui-monospace, Consolas, monospace;
  --raio: 4px;
  color-scheme: light;
}}
body {{ margin: 0; background: var(--fundo); color: var(--tinta); font-family: var(--fonte-texto); font-size: 15px; line-height: 1.6; }}
.container {{ max-width: 48rem; margin: 0 auto; padding-block: 2.5rem 4rem;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 3rem; }}
h1, h2, h3 {{ font-family: var(--fonte-display); font-weight: 400; line-height: 1.15; margin: 0; text-wrap: balance; }}
h1 {{ font-size: clamp(2rem, 6vw, 2.75rem); }}
h2 {{ font-size: 1.5rem; }}
h3 {{ font-size: 1.05rem; }}
p {{ margin: 0; }}
a {{ color: var(--marca); }}
a:focus-visible, .botao:focus-visible, summary:focus-visible {{ outline: 2px solid var(--marca); outline-offset: 2px; }}
section {{ display: grid; gap: 1rem; min-width: 0; }}
.secao-topo {{ display: grid; gap: .25rem; }}
.sobretitulo {{ font-family: var(--fonte-mono); font-size: .75rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--marca); }}
.lead {{ color: var(--tinta-suave); font-size: 1.05rem; }}
.mono {{ font-family: var(--fonte-mono); font-size: .85rem; }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.numero-grande {{ font-family: var(--fonte-mono); font-size: 3rem; font-weight: 600; line-height: 1; font-variant-numeric: tabular-nums; }}
.numero-grande small {{ font-size: 1.5rem; color: var(--tinta-suave); }}
.card {{ background: var(--superficie); border: 1px solid var(--borda); border-radius: var(--raio); padding: 1rem 1.25rem; display: grid; gap: .75rem; min-width: 0; }}
.card-topo {{ display: flex; align-items: center; justify-content: space-between; gap: .5rem; flex-wrap: wrap; }}
.etiqueta {{ font-size: .75rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: #fff;
  background: var(--vermelho); padding: .2rem .5rem; border-radius: var(--raio); white-space: nowrap; }}
.etiqueta.verde {{ background: var(--verde); }}
.etiqueta.vermelho {{ background: var(--vermelho); }}
.etiqueta.laranja {{ background: var(--laranja); }}
.etiqueta.amarelo {{ background: var(--amarelo); color: var(--tinta); }}
.etiqueta.cinza {{ background: var(--cinza); }}
.card-meta {{ font-family: var(--fonte-mono); font-size: .8rem; color: var(--tinta-suave); }}
.card-meta a {{ color: var(--marca); text-decoration: none; }}
.card-acoes {{ display: flex; flex-wrap: wrap; gap: .5rem; }}
.botao {{ display: inline-block; padding: .45rem .9rem; border: 1px solid var(--tinta); border-radius: var(--raio); color: var(--tinta);
  background: transparent; font: 600 .875rem var(--fonte-texto); text-decoration: none; cursor: pointer; }}
.botao-primario {{ background: var(--marca); border-color: var(--marca); color: #fff; }}
.barra {{ height: 8px; border-radius: var(--raio); background: var(--vermelho); overflow: hidden; }}
.barra span {{ display: block; height: 100%; background: var(--verde); }}
.meta {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem 1.5rem; margin: 0; padding-top: .75rem; border-top: 1px solid var(--borda); }}
.meta div {{ display: grid; gap: .1rem; min-width: 0; }}
.meta dt {{ font-family: var(--fonte-mono); font-size: .7rem; letter-spacing: .06em; text-transform: uppercase; color: var(--tinta-suave); }}
.meta dd {{ margin: 0; overflow-wrap: anywhere; }}
.contagem {{ display: flex; flex-wrap: wrap; gap: .5rem; }}
video, .caso-corpo img {{ width: 100%; display: block; border: 1px solid var(--borda); border-radius: var(--raio); background: var(--fundo); }}
.card video:not([poster^="screenshots"]) {{ background: #111; aspect-ratio: 1366 / 900; }}
.legenda {{ font-size: .8rem; color: var(--tinta-suave); }}
ul.lista {{ margin: 0; padding-left: 1.1rem; display: grid; gap: .35rem; }}
.tabela {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: .9rem; }}
th {{ text-align: left; font-family: var(--fonte-mono); font-size: .7rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase;
  color: var(--tinta-suave); padding: .4rem .5rem; border-bottom: 1px solid var(--borda); white-space: nowrap; }}
td {{ padding: .5rem; border-bottom: 1px solid var(--borda); vertical-align: top; }}
tr:last-child td {{ border-bottom: 0; }}
td:first-child {{ width: 3.5rem; }}
.nota {{ display: block; color: var(--vermelho); font-size: .8rem; font-weight: 600; }}
.sugestao {{ color: var(--tinta-suave); font-size: .9rem; }}
details.caso {{ padding: 0; gap: 0; }}
details.caso + details.caso {{ margin-top: .5rem; }}
summary {{ cursor: pointer; padding: .75rem 1.25rem; display: flex; align-items: center; gap: .75rem; list-style: none; }}
summary::-webkit-details-marker {{ display: none; }}
summary::before {{ content: "+"; font-family: var(--fonte-mono); font-weight: 600; color: var(--marca); width: .75rem; }}
details[open] summary::before {{ content: "−"; }}
.codigo {{ color: var(--tinta-suave); }}
.sum-titulo {{ flex: 1; min-width: 0; font-weight: 500; }}
.caso-corpo {{ display: grid; gap: .75rem; padding: 0 1.25rem 1.25rem; min-width: 0; }}
pre {{ margin: 0; font: .82rem/1.6 var(--fonte-mono); background: var(--codigo); border-radius: var(--raio); padding: .85rem 1rem; overflow-x: auto; white-space: pre-wrap; }}
.gherkin .kw {{ color: var(--marca); font-weight: 600; }}
.gherkin .str {{ color: #8a4b00; }}
pre.erro {{ background: #fde3e6; color: #a00d20; }}
.passos {{ margin: 0; padding: 0; list-style: none; display: grid; gap: 1.25rem; }}
.passos li {{ display: grid; grid-template-columns: 2.5rem minmax(0, 1fr); gap: 1rem; }}
.passo-num {{ font-family: var(--fonte-mono); font-size: 1.75rem; font-weight: 600; color: var(--marca); line-height: 1.1; }}
.passos li > div {{ display: grid; gap: .4rem; min-width: 0; }}
.passos p {{ font-size: .92rem; }}
code {{ font-family: var(--fonte-mono); font-size: .82rem; background: var(--codigo); padding: .05rem .3rem; border-radius: var(--raio); }}
.cmd {{ display: flex; align-items: center; gap: .5rem; background: var(--superficie); border: 1px solid var(--borda); border-radius: var(--raio); padding: .4rem .4rem .4rem .8rem; min-width: 0; }}
.cmd code {{ flex: 1; min-width: 0; overflow-x: auto; white-space: nowrap; background: none; padding: 0; }}
.copiar {{ padding: .25rem .7rem; font-size: .8rem; }}
.rodape {{ color: var(--tinta-suave); font-size: .85rem; border-top: 1px solid var(--borda); padding-top: 1rem; }}
@media (max-width: 520px) {{ .meta {{ grid-template-columns: minmax(0, 1fr); }} .numero-grande {{ font-size: 2.5rem; }} }}
</style>
<div class="container">
  <header class="secao-topo">
    <span class="sobretitulo">ECOM021 · Engenharia de Software · testes de ponta a ponta</span>
    <h1>Testes do Aluguel de Imóveis</h1>
    <p class="lead">{total} cenários em Gherkin, automatizados com Playwright e pytest, rodando pelo navegador contra o sistema de aluguel com microsserviços.</p>
  </header>

  <article class="card" aria-label="Placar">
    <div class="card-topo">
      <span class="etiqueta verde">Placar</span>
      <span class="card-meta">{data} · {tempo}</span>
    </div>
    <div class="numero-grande">{aprovados}<small>/{total} aprovados</small></div>
    <div class="barra" role="img" aria-label="{porcento}% aprovados"><span style="width: {porcento}%"></span></div>
    <p>{falhas} falhas, as duas por defeito real do sistema. Nenhuma falha de teste na execução final.</p>
    <dl class="meta">
      <div><dt>Sistema testado</dt><dd class="mono">{url}</dd></div>
      <div><dt>Navegador</dt><dd>{navegador}</dd></div>
      <div><dt>Tamanhos de tela</dt><dd>Desktop 1366 × 900 · celular 390 × 844</dd></div>
      <div><dt>Achados</dt><dd>{defeitos} defeitos · {observacoes} observações · {melhorias} melhorias</dd></div>
    </dl>
    <div class="card-acoes">
      <a class="botao botao-primario" href="#achados">Ver os achados</a>
      <a class="botao" href="#resultados">Ver os resultados</a>
    </div>
  </article>

  <section>
    <div class="secao-topo"><span class="sobretitulo">Demonstração</span><h2>O sistema em funcionamento</h2></div>
    <article class="card">
      <div class="card-topo"><span class="etiqueta cinza">Vídeo narrado</span><span class="card-meta">6 min 14 s · 1366 × 900</span></div>
      <video controls preload="metadata" poster="capa.jpg" src="demonstracao_narrada.mp4"></video>
      <p>Jornada completa com narração: arquitetura pelo gateway, catálogo, contratos, usuários, notificações, recomendação, agente e os três perfis.</p>
    </article>
  </section>

  <section>
    <div class="secao-topo"><span class="sobretitulo">Escopo</span><h2>O que foi testado</h2></div>
    <article class="card"><div class="card-topo"><span class="etiqueta verde">Dentro</span></div><ul class="lista">{dentro}</ul></article>
    <article class="card"><div class="card-topo"><span class="etiqueta cinza">Fora</span></div><ul class="lista">{fora}</ul></article>
    <article class="card"><div class="card-topo"><span class="etiqueta laranja">Abordagem</span></div><ul class="lista">{abordagem}</ul></article>
  </section>

  <section id="resultados">
    <div class="secao-topo"><span class="sobretitulo">Resultados</span><h2>Por módulo</h2></div>
    {tabelas}
  </section>

  <section id="achados">
    <div class="secao-topo"><span class="sobretitulo">Achados</span><h2>O que precisa de atenção</h2></div>
    <div class="contagem">
      <span class="etiqueta vermelho">{defeitos} defeitos</span>
      <span class="etiqueta laranja">{observacoes} observações</span>
      <span class="etiqueta amarelo">{melhorias} melhorias</span>
    </div>
    {achados}
  </section>

  <section>
    <div class="secao-topo"><span class="sobretitulo">Evidências</span><h2>Cada caso</h2></div>
    <p>Abra um caso para ver o cenário em Gherkin, a tela ao final da execução e o vídeo dele.</p>
    <div>{detalhes}</div>
  </section>

  <section>
    <div class="secao-topo"><span class="sobretitulo">Como rodar</span><h2>No seu computador (Windows)</h2></div>
    <ol class="passos">{passos}</ol>
  </section>

  <p class="rodape">Suíte na pasta <span class="mono">e2e/</span> do repositório github.com/3runorocha/ECOM021-eng-de-software. Os bancos são copiados antes da execução e restaurados antes de cada caso e no fim, então o sistema termina como estava.</p>
</div>
<script>
document.querySelectorAll(".copiar").forEach(function (botao) {{
  botao.addEventListener("click", function () {{
    var texto = botao.dataset.cmd;
    var pronto = function () {{ botao.textContent = "Copiado"; setTimeout(function () {{ botao.textContent = "Copiar"; }}, 1500); }};
    try {{
      navigator.clipboard.writeText(texto).then(pronto, function () {{ selecionar(botao); }});
    }} catch (erro) {{ selecionar(botao); }}
  }});
}});
function selecionar(botao) {{
  var faixa = document.createRange();
  faixa.selectNodeContents(botao.previousElementSibling);
  var selecao = window.getSelection();
  selecao.removeAllRanges();
  selecao.addRange(faixa);
}}
document.querySelectorAll("a[href^='#ct']").forEach(function (link) {{
  link.addEventListener("click", function () {{
    var alvo = document.querySelector(link.getAttribute("href"));
    if (alvo) {{ alvo.open = true; }}
  }});
}});
if (location.hash && /^#ct\\d+$/.test(location.hash)) {{
  var aberto = document.querySelector(location.hash);
  if (aberto) {{ aberto.open = true; }}
}}
</script>
"""


if __name__ == "__main__":
    montar()
    copiar_midias()
    print(f"Relatório em {SAIDA / 'index.html'}")

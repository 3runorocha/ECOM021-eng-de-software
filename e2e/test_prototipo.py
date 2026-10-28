"""Casos de ponta a ponta do sistema de aluguel, pelo navegador.

Cada teste corresponde a um cenário de `casos.feature`, com o mesmo código
(CT01, CT02...). Os dados esperados são os do seed de exemplo: 18 imóveis,
9 deles alugados, e 42 contratos.
"""
import re

from playwright.sync_api import expect

from apoio import FRONT, entrar, ir


def contagem(page):
    return page.locator("text=/\\d+ imóvel\\(is\\)/")


def card_do_imovel(page, titulo):
    return page.locator("main div", has=page.locator(f"text='{titulo}'")).filter(
        has_text=re.compile("Disponível|Alugado")).last


def abrir_form_contrato(page):
    page.click("text=+ Novo contrato")
    form = page.locator("form")
    expect(form).to_be_visible()
    return form


def test_ct01_login_valido_abre_o_painel(abrir):
    page = abrir()
    entrar(page, "admin")
    main = page.locator("main")
    for rotulo in ("Imóveis", "Contratos em vigor", "Usuários"):
        expect(main).to_contain_text(rotulo)
    expect(page.locator("aside")).to_contain_text("Admin")


def test_ct02_login_com_senha_errada(abrir):
    page = abrir()
    page.goto(FRONT + "/")
    page.fill("input[type=email]", "admin@alugue.br")
    page.fill("input[type=password]", "errada")
    page.click("button[type=submit]")
    expect(page.locator("text=Email ou senha inválidos")).to_be_visible()
    expect(page.locator("input[type=password]")).to_be_visible()


def test_ct03_login_exige_os_campos(abrir):
    page = abrir()
    page.goto(FRONT + "/")
    page.click("button[type=submit]")
    invalidos = page.evaluate(
        "() => [...document.querySelectorAll('input')].filter(i => !i.checkValidity()).length")
    assert invalidos == 2
    expect(page.locator("text=Sair")).to_have_count(0)


def test_ct04_sessao_continua_depois_de_recarregar(abrir):
    page = abrir()
    entrar(page, "admin")
    page.reload()
    expect(page.locator("text=Sair")).to_be_visible()


def test_ct05_sair_encerra_a_sessao(abrir):
    page = abrir()
    entrar(page, "admin")
    page.click("text=Sair")
    expect(page.locator("input[type=email]")).to_be_visible()
    page.goto(FRONT + "/contratos")
    expect(page.locator("input[type=email]")).to_be_visible()
    expect(page.locator("text=+ Novo contrato")).to_have_count(0)


def test_ct06_menu_leva_a_todas_as_telas(abrir):
    page = abrir()
    entrar(page, "admin")
    telas = {
        "/imoveis": "imóvel(is)",
        "/contratos": "+ Novo contrato",
        "/usuarios": "Buscar por nome ou e-mail",
        "/notificacoes": "Rodar varredura",
        "/recomendacao": "Recomendar imóveis",
        "/agente": "Busca em linguagem natural",
        "/": "Contratos em vigor",
    }
    for rota, marca in telas.items():
        page.click(f"aside a[href='{rota}']")
        expect(page).to_have_url(FRONT + rota)
        if "Buscar" in marca:
            expect(page.locator(f"input[placeholder^='{marca}']")).to_be_visible()
        else:
            expect(page.locator("main")).to_contain_text(marca)


def test_ct07_painel_mostra_numeros_reais(abrir):
    page = abrir()
    entrar(page, "admin")
    main = page.locator("main")
    expect(main).to_contain_text("9 disponíveis")
    expect(main).to_contain_text("3 em atraso")
    expect(main).to_contain_text("R$ 30.480")
    textos = main.inner_text()
    assert re.search(r"Imóveis\s+18", textos), textos[:300]
    assert re.search(r"Contratos em vigor\s+9", textos), textos[:300]
    assert re.search(r"Usuários\s+7", textos), textos[:300]
    status = page.locator("aside")
    for servico in ("Gateway", "Imóveis", "Usuários", "Contratos", "Notificações", "Recomendação", "Agente"):
        expect(status).to_contain_text(re.compile(f"{servico} — :80"))


def test_ct08_catalogo_carrega(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/imoveis")
    expect(contagem(page)).to_have_text("18 imóvel(is)")
    disponiveis = page.locator("main >> text='Disponível'").count()
    alugados = page.locator("main >> text='Alugado'").count()
    assert (disponiveis, alugados) == (9, 9)


def test_ct09_busca_com_resultado(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/imoveis")
    page.fill("input[placeholder^='Buscar']", "Boa Viagem")
    expect(contagem(page)).to_have_text("2 imóvel(is)")


def test_ct10_busca_sem_resultado(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/imoveis")
    page.fill("input[placeholder^='Buscar']", "xyz inexistente")
    expect(page.locator("text=Nenhum imóvel para esses filtros.")).to_be_visible()
    expect(contagem(page)).to_have_count(0)


def test_ct11_filtro_de_cidade_ignora_acento(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/imoveis")
    cidade = page.locator("input[placeholder='qualquer']")
    cidade.fill("Maceió")
    expect(contagem(page)).to_have_text("8 imóvel(is)")
    cidade.fill("maceio")
    expect(contagem(page)).to_have_text("8 imóvel(is)")


def test_ct12_combinar_filtros_e_limpar(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/imoveis")
    page.fill("input[placeholder='qualquer']", "Maceió")
    expect(contagem(page)).to_have_text("8 imóvel(is)")
    filtros = page.locator("main select")
    filtros.nth(0).select_option("casa")
    expect(contagem(page)).to_have_text("2 imóvel(is)")
    filtros.nth(2).select_option("true")
    expect(contagem(page)).to_have_text("1 imóvel(is)")
    page.fill("input[placeholder='sem limite']", "2000")
    expect(contagem(page)).to_have_text("1 imóvel(is)")
    expect(page.locator("main")).to_contain_text("Casa no Tabuleiro")
    page.click("text=Limpar")
    expect(contagem(page)).to_have_text("18 imóvel(is)")
    expect(page.locator("input[placeholder='qualquer']")).to_have_value("")


def test_ct13_abrir_e_cancelar_formulario_de_imovel(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/imoveis")
    page.click("text=+ Novo imóvel")
    form = page.locator("form")
    expect(form).to_be_visible()
    for campo in ("Título", "Endereço", "Cidade", "Quartos", "Banheiros", "Área (m²)", "Aluguel mensal (R$)"):
        expect(form).to_contain_text(campo)
    form.locator("text=Cancelar").click()
    expect(page.locator("form")).to_have_count(0)


def test_ct14_novo_imovel_exige_campos(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/imoveis")
    page.click("text=+ Novo imóvel")
    page.locator("form button[type=submit]").click()
    invalidos = page.evaluate(
        "() => [...document.querySelectorAll('form input')].filter(i => !i.checkValidity()).length")
    assert invalidos == 7
    expect(page.locator("form")).to_be_visible()
    expect(contagem(page)).to_have_text("18 imóvel(is)")


def test_ct15_cadastrar_imovel(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/imoveis")
    page.click("text=+ Novo imóvel")
    form = page.locator("form")
    form.locator("select").select_option("casa")
    textos = form.locator("input[type=text]")
    textos.nth(0).fill("Casa de Teste na Ponta Verde")
    textos.nth(1).fill("Rua do Teste, 10")
    textos.nth(2).fill("Maceió")
    for indice, valor in enumerate(["3", "2", "120", "2800"]):
        form.locator("input[type=number]").nth(indice).fill(valor)
    form.locator("button[type=submit]").click()
    expect(page.locator("form")).to_have_count(0)
    expect(contagem(page)).to_have_text("19 imóvel(is)")
    expect(card_do_imovel(page, "Casa de Teste na Ponta Verde")).to_contain_text("Disponível")


def test_ct16_inquilina_nao_cadastra_imovel(abrir):
    page = abrir()
    entrar(page, "ana")
    ir(page, "/imoveis")
    expect(contagem(page)).to_have_text("18 imóvel(is)")
    expect(page.locator("text=+ Novo imóvel")).to_have_count(0)


def test_ct17_formulario_de_contrato_exige_campos(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/contratos")
    linhas = page.locator("tbody tr")
    expect(linhas).to_have_count(42)
    form = abrir_form_contrato(page)
    form.locator("button[type=submit]").click()
    invalidos = page.evaluate(
        "() => [...document.querySelectorAll('form select')].filter(s => !s.checkValidity()).length")
    assert invalidos == 2
    expect(form).to_be_visible()
    expect(linhas).to_have_count(42)


def assinar_serraria_para_ana(page):
    form = abrir_form_contrato(page)
    expect(form).to_contain_text("Imóvel disponível (9)")
    form.locator("select").nth(0).select_option(label="Ana Souza")
    imovel = form.locator("option", has_text="Apartamento no Serraria").get_attribute("value")
    form.locator("select").nth(1).select_option(imovel)
    form.locator("button[type=submit]").click()
    ativa = page.locator("tbody tr", has_text="Apartamento no Serraria").filter(has_text="Ativo")
    expect(ativa).to_have_count(1)
    numero = ativa.locator("td").first.inner_text().strip()
    return page.locator("tbody tr", has=page.locator(f"td:text-is('{numero}')"))


def test_ct18_assinar_contrato_ocupa_o_imovel(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/contratos")
    linha = assinar_serraria_para_ana(page)
    expect(linha).to_contain_text("Ana Souza")
    form = abrir_form_contrato(page)
    expect(form).to_contain_text("Imóvel disponível (8)")
    expect(form.locator("option", has_text="Apartamento no Serraria")).to_have_count(0)
    ir(page, "/imoveis")
    expect(card_do_imovel(page, "Apartamento no Serraria")).to_contain_text("Alugado")


def test_ct19_encerrar_contrato_libera_o_imovel(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/contratos")
    linha = assinar_serraria_para_ana(page)
    linha.locator("text=Encerrar").click()
    expect(linha).to_contain_text("Encerrado")
    datas = re.findall(r"\d{4}-\d{2}-\d{2}", linha.inner_text())
    assert len(datas) == 3, "fim real não foi preenchido: " + linha.inner_text()
    ir(page, "/imoveis")
    expect(card_do_imovel(page, "Apartamento no Serraria")).to_contain_text("Disponível")


def test_ct20_filtro_de_atrasados(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/contratos")
    page.locator("main select").first.select_option("atrasado")
    linhas = page.locator("tbody tr")
    expect(linhas).to_have_count(3)
    for i in range(3):
        expect(linhas.nth(i)).to_contain_text("Atrasado")
        expect(linhas.nth(i)).to_contain_text(re.compile(r"venceu há \d+ dia\(s\)"))


def test_ct21_inquilina_so_ve_os_proprios_contratos(abrir):
    page = abrir()
    entrar(page, "ana")
    ir(page, "/contratos")
    linhas = page.locator("tbody tr")
    expect(linhas).to_have_count(6)
    for i in range(6):
        expect(linhas.nth(i)).to_contain_text("Ana Souza")
    form = abrir_form_contrato(page)
    opcoes = form.locator("select").nth(0).locator("option").all_inner_texts()
    assert [o for o in opcoes if o != "selecione"] == ["Ana Souza"], opcoes


def test_ct22_admin_promove_inquilino(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/usuarios")
    linha = page.locator("tr", has_text="joao@alugue.br")
    linha.locator("select").select_option("proprietario")
    expect(page.locator("tr", has_text="joao@alugue.br").locator("select")).to_have_value("proprietario")

    joao = abrir()
    entrar(joao, "joao")
    ir(joao, "/imoveis")
    expect(joao.locator("text=+ Novo imóvel")).to_be_visible()


def test_ct23_inquilina_nao_muda_perfil(abrir):
    page = abrir()
    entrar(page, "ana")
    ir(page, "/usuarios")
    expect(page.locator("tbody tr")).to_have_count(7)
    expect(page.locator("main select")).to_have_count(0)


def test_ct24_varredura_e_marcar_como_lida(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/notificacoes")
    expect(page.locator("main")).to_contain_text("0 não lida(s) de 0")
    page.click("text=Rodar varredura")
    expect(page.locator("main")).to_contain_text("1 não lida(s) de 1")
    expect(page.locator("main")).to_contain_text("venceu há")
    page.click("text=Marcar lida")
    expect(page.locator("main")).to_contain_text("0 não lida(s) de 1")


def test_ct25_recomendacao_pelo_historico(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/recomendacao")
    page.locator("main select").first.select_option(label="Ana Souza")
    page.click("text=Recomendar imóveis")
    main = page.locator("main")
    expect(main).to_contain_text("Perfil calculado")
    expect(main).to_contain_text("6 contrato(s) no histórico")
    expect(main).to_contain_text("está entre seus preferidos")
    expect(main.locator("text=/\\d / 5/").first).to_be_visible()


def test_ct26_inquilina_consulta_so_a_propria_recomendacao(abrir):
    page = abrir()
    entrar(page, "ana")
    ir(page, "/recomendacao")
    seletor = page.locator("main select").first
    opcoes = seletor.locator("option").all_inner_texts()
    assert seletor.input_value() == "2", (
        f"a tela abriu no usuário {seletor.input_value()}, não na Ana (2)")
    assert opcoes == ["Ana Souza"], f"a inquilina pode consultar outros usuários: {opcoes}"


def test_ct27_agente_sem_credencial(abrir):
    page = abrir()
    entrar(page, "admin")
    ir(page, "/agente")
    expect(page.locator("main")).to_contain_text("Agente sem credencial")
    page.fill("input[placeholder='O que você procura?']", "casa em Maceio")
    page.click("main button[type=submit]")
    expect(page.locator("main")).to_contain_text("Defina ANTHROPIC_API_KEY no ambiente")


def test_ct28_mobile_sem_rolagem_horizontal(abrir):
    page = abrir("mobile")
    entrar(page, "admin")
    for rota in ("/", "/imoveis", "/contratos"):
        ir(page, rota)
        largura = page.evaluate("() => document.documentElement.scrollWidth")
        assert largura <= 390, f"{rota} rola na horizontal: {largura}px"


def test_ct29_mobile_mostra_o_conteudo(abrir):
    page = abrir("mobile")
    entrar(page, "admin")
    ir(page, "/contratos")
    area = page.locator("main").bounding_box()
    assert area["width"] >= 390 * 0.75, (
        f"o conteúdo ocupa só {area['width']:.0f}px de 390px; o menu lateral fica fixo ao lado")
    botao = page.locator("text=+ Novo contrato").bounding_box()
    assert botao["x"] + botao["width"] <= 390, "o botão + Novo contrato fica cortado"

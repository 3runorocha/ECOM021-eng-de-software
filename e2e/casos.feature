# language: pt

Funcionalidade: Acesso ao sistema
  Como usuário do sistema de aluguel
  Quero entrar com e-mail e senha
  Para usar apenas o que o meu perfil permite

  Cenário: CT01 Login com credenciais válidas abre o painel
    Dado que estou na tela de login
    Quando entro com "admin@alugue.br" e a senha correta
    Então vejo o painel com o resumo de imóveis, contratos e usuários
    E vejo meu nome e o botão "Sair" no menu

  Cenário: CT02 Login com senha errada é recusado
    Dado que estou na tela de login
    Quando entro com "admin@alugue.br" e a senha "errada"
    Então vejo a mensagem "Email ou senha inválidos"
    E continuo na tela de login

  Cenário: CT03 Login exige e-mail e senha
    Dado que estou na tela de login
    Quando clico em "Entrar" sem preencher os campos
    Então o navegador marca os dois campos como obrigatórios
    E o formulário não é enviado

  Cenário: CT04 Sessão continua depois de recarregar a página
    Dado que entrei como admin
    Quando recarrego a página
    Então continuo logado, com o botão "Sair" visível

  Cenário: CT05 Sair encerra a sessão e protege as rotas
    Dado que entrei como admin
    Quando clico em "Sair"
    Então volto para a tela de login
    E ao abrir "/contratos" direto pelo endereço continuo na tela de login

Funcionalidade: Navegação e painel

  Cenário: CT06 Menu lateral leva a todas as telas
    Dado que entrei como admin
    Quando clico em cada item do menu
    Então o endereço muda para a tela correspondente
    E cada tela mostra o próprio conteúdo

  Cenário: CT07 Painel mostra números reais do sistema
    Dado que o sistema está com os dados de exemplo
    Quando entro como admin
    Então o painel mostra 18 imóveis, 9 disponíveis
    E 9 contratos em vigor, 3 em atraso
    E receita mensal de R$ 30.480 e 7 usuários
    E o menu lista o status dos 7 serviços

Funcionalidade: Catálogo de imóveis

  Cenário: CT08 Catálogo carrega os imóveis
    Dado que entrei como admin
    Quando abro a tela de imóveis
    Então vejo "18 imóvel(is)" com situação "Disponível" ou "Alugado" em cada um

  Cenário: CT09 Busca com resultado
    Dado que estou no catálogo
    Quando busco por "Boa Viagem"
    Então vejo "2 imóvel(is)"

  Cenário: CT10 Busca sem resultado mostra estado vazio
    Dado que estou no catálogo
    Quando busco por "xyz inexistente"
    Então vejo "Nenhum imóvel para esses filtros."

  Cenário: CT11 Filtro de cidade ignora acento e caixa
    Dado que estou no catálogo
    Quando filtro a cidade por "Maceió"
    Então vejo "8 imóvel(is)"
    E ao filtrar por "maceio" vejo os mesmos 8

  Cenário: CT12 Combinar filtros e limpar
    Dado que estou no catálogo
    Quando filtro por cidade "Maceió", tipo "casa", situação "disponível" e aluguel até 2000
    Então vejo só "Casa no Tabuleiro"
    E ao clicar em "Limpar" volto a ver "18 imóvel(is)"

  Cenário: CT13 Abrir e cancelar o formulário de novo imóvel
    Dado que entrei como admin no catálogo
    Quando clico em "+ Novo imóvel"
    Então o formulário aparece com os campos do imóvel
    E ao clicar em "Cancelar" o formulário fecha

  Cenário: CT14 Novo imóvel exige os campos obrigatórios
    Dado que abri o formulário de novo imóvel
    Quando clico em "Salvar" sem preencher nada
    Então os 7 campos obrigatórios ficam marcados
    E o catálogo continua com 18 imóveis

  Cenário: CT15 Cadastrar imóvel
    Dado que abri o formulário de novo imóvel
    Quando preencho título, endereço, cidade, quartos, banheiros, área e aluguel e salvo
    Então o formulário fecha
    E o catálogo passa a ter 19 imóveis, com o novo marcado como "Disponível"

  Cenário: CT16 Inquilina não cadastra imóvel
    Dado que entrei como a inquilina Ana
    Quando abro o catálogo
    Então não vejo o botão "+ Novo imóvel"

Funcionalidade: Contratos

  Cenário: CT17 Formulário de contrato exige inquilino e imóvel
    Dado que entrei como admin na tela de contratos
    Quando abro "+ Novo contrato" e clico em "Registrar" sem escolher nada
    Então os dois campos ficam marcados como obrigatórios

  Cenário: CT18 Assinar contrato ocupa o imóvel
    Dado que entrei como admin na tela de contratos
    Quando registro um contrato da Ana no "Apartamento no Serraria"
    Então o contrato aparece como "Ativo"
    E o imóvel sai da lista de disponíveis, que cai de 9 para 8
    E no catálogo o imóvel aparece como "Alugado"

  Cenário: CT19 Encerrar contrato libera o imóvel
    Dado que existe um contrato ativo da Ana no "Apartamento no Serraria"
    Quando clico em "Encerrar" nesse contrato
    Então ele passa a "Encerrado", com a data de fim real preenchida
    E no catálogo o imóvel volta a aparecer como "Disponível"

  Cenário: CT20 Filtro de status mostra só os atrasados
    Dado que entrei como admin na tela de contratos
    Quando escolho o status "Atrasados"
    Então vejo apenas contratos "Atrasado", cada um com "venceu há N dia(s)"

  Cenário: CT21 Inquilina só vê e só assina os próprios contratos
    Dado que entrei como a inquilina Ana
    Quando abro a tela de contratos
    Então todos os contratos listados são da Ana
    E no formulário de novo contrato o único inquilino possível é ela

Funcionalidade: Usuários

  Cenário: CT22 Admin promove inquilino a proprietário
    Dado que entrei como admin na tela de usuários
    Quando mudo o perfil de "Joao Melo" para "proprietario"
    Então a linha dele mostra o novo perfil
    E ao entrar como João ele passa a ver "+ Novo imóvel"

  Cenário: CT23 Inquilina não muda perfil de ninguém
    Dado que entrei como a inquilina Ana
    Quando abro a tela de usuários
    Então vejo a lista sem nenhum seletor de perfil

Funcionalidade: Notificações

  Cenário: CT24 Varredura gera alerta e marcar como lida atualiza o contador
    Dado que entrei como admin na tela de notificações, sem nenhuma notificação
    Quando clico em "Rodar varredura"
    Então aparece um alerta de atraso e o contador mostra "1 não lida(s) de 1"
    E ao clicar em "Marcar lida" o contador passa a "0 não lida(s) de 1"

Funcionalidade: Recomendação

  Cenário: CT25 Recomendação a partir do histórico
    Dado que entrei como admin na tela de recomendação
    Quando escolho "Ana Souza" e clico em "Recomendar imóveis"
    Então vejo o perfil calculado com 6 contratos no histórico
    E imóveis disponíveis pontuados, com o motivo da pontuação

  Cenário: CT26 Inquilina consulta só a própria recomendação
    Dado que entrei como a inquilina Ana
    Quando abro a tela de recomendação
    Então o seletor vem com ela mesma escolhida
    E não oferece outros usuários

Funcionalidade: Agente de IA

  Cenário: CT27 Agente sem credencial avisa e responde com clareza
    Dado que o serviço do agente está no ar sem chave da Anthropic
    Quando abro a tela do agente e pergunto "casa em Maceio"
    Então vejo o aviso "Agente sem credencial"
    E a resposta explica que falta definir ANTHROPIC_API_KEY

Funcionalidade: Responsivo

  Cenário: CT28 Mobile 390px sem rolagem horizontal
    Dado que entrei como admin num celular de 390px
    Quando abro o painel, o catálogo e os contratos
    Então nenhuma das telas tem rolagem horizontal na página

  Cenário: CT29 Mobile 390px mostra o conteúdo principal
    Dado que entrei como admin num celular de 390px
    Quando abro a tela de contratos
    Então a área de conteúdo ocupa a maior parte da largura
    E o botão "+ Novo contrato" fica inteiro dentro da tela

# Validação semanal

Ao fim de cada semana, antes de começar o bloco seguinte. Serve para duas coisas:
não construir em cima de algo quebrado, e ter o que mostrar de progresso.

## O ritual

```bash
git pull
python validar.py
```

Se passar tudo, o script diz `Tudo passou. Pode seguir para o proximo bloco.`
e sai com código 0. Se algo falhar, ele nomeia a checagem, explica o que esperava
e sai com código 1.

Depois, a checagem manual da semana (tabela abaixo) e o commit do que faltou.

`python validar.py --estatico` roda só o que não precisa subir serviço — útil
quando você já está com os serviços no ar e não quer derrubá-los.

## O que o script cobre

As checagens vivas sobem os 6 serviços com **bancos temporários**, então rodar o
validador não suja seus dados de desenvolvimento.

| Bloco | Checagem | O que pegaria |
|-------|----------|---------------|
| 1 | framework exige os dois hotspots | alguém redefinir um hotspot abstrato como método concreto |
| 1 | nenhuma URL hardcoded | URL de serviço voltando a ser literal, com arquivo e linha |
| 1 | env var sobrescreve a URL | `getenv` presente mas sem efeito |
| 1 | bancos vêm de env var | `DB_PATH` voltando a ser literal |
| 2 | sem API depreciada | `@app.on_event` voltando, ou `lifespan` não registrado |
| 2 | proxy filtra headers do corpo | `content-encoding`/`content-length` sendo repassados |
| 2 | health geral com os 6 no ar | qualquer serviço que não sobe |
| 2 | fluxo completo pelo gateway | registro → login → cadastro → leitura quebrando |
| 2 | resposta comprimida intacta | corpo corrompido por header obsoleto |
| 2 | rota protegida exige token | autenticação furada (sem token ou token falso passando) |
| 2 | shutdown liberou as 6 portas | processo órfão segurando porta |
| — | todo `.py` compila | erro de sintaxe em qualquer arquivo |
| 3 | modelo Imovel substituiu o Livro | campo de acervo (isbn, genero, autor, quantidade) voltando ao modelo |
| 4 | componente usa disponibilidade booleana | `IComponenteImovel` sem `definir_disponibilidade`, ou `IComponenteCatalogo` ressuscitado |
| 4 | filtros de imóvel filtram | cidade/tipo/quartos_min/valor vazando resultado errado |
| 4 | disponibilidade é booleana | guarda de estado sumindo (alugar imóvel já alugado deve dar 400) |
| 6 | modelo Contrato substituiu o Emprestimo | `usuario_id`/`livro_id`/`data_emprestimo` voltando ao modelo |
| 7 | prazo em meses e multa proporcional | `PRAZO_MESES` ≠ 12, `MULTA_POR_DIA` fixo voltando, ou `somar_meses` errando mês curto (31/01 + 1 mês) |
| 8 | ciclo de contrato completo | assinar → ocupar imóvel → encerrar → liberar quebrando em qualquer ponto |
| 8 | um contrato aberto por imóvel | segundo contrato no mesmo imóvel passando, ou imóvel ficando solto pela compensação |
| 10 | página de imóveis substituiu o catálogo | `Catalogo.jsx` ressuscitando, ou `App.jsx` sem a rota `/imoveis` |
| 10 | frontend não inventa dados | fallback de dados falsos em **qualquer** página, página sem estado de erro, ou status de serviço fixo em `ok: true` no Sidebar |
| 10 | frontend compila | build do Vite quebrando (pula com aviso se faltar `npm install`) |
| 11 | página de contratos substituiu empréstimos | `Emprestimos.jsx` ressuscitando, rota faltando, ou a tela voltando a falar de status `devolvido` |
| 11 | tela não duplica a regra de multa | o frontend passando a fazer conta com `valor_mensal` — a multa é do serviço |
| 12 | configurador foi removido | a tela da LPS antiga voltando, ou rota/menu órfãos |
| 12 | frontend sem vocabulário de biblioteca | `livro`, `autor`, `genero` ou `emprestimo` reaparecendo em qualquer tela |
| 12 | recomendação responde rápido | chamada entre serviços lenta (host errado derruba para ~2s por chamada) |
| 13 | agente usa a camada de componentes | o agente virando cliente HTTP paralelo em vez de usar `framework/componentes.py` |
| 13 | ferramentas do agente são de leitura | ferramenta de escrita (registrar/encerrar contrato, mudar disponibilidade) exposta ao modelo |
| 13 | agente usa modelo atual | id de modelo inventado ou com sufixo de data (esses dão 404) |
| 13 | agente degrada sem credencial | falta de chave virando 500 em vez de 503 com instrução. **Não chama o modelo quando há credencial** — validador não pode gastar dinheiro a cada execução |
| 14 | agente é componente do framework | `IComponenteAgente`/`ComponenteAgenteHTTP` sumindo — é o que permite a App orquestrar o agente |
| 14 | app do framework orquestra o agente | a app deixando de estender o framework, sobrescrevendo `executar_operacao`, ou falando HTTP direto |
| 14 | redator de aviso não faz conta | o prompt deixando o modelo calcular multa ou inventar fato |
| 14 | aviso sai mesmo com agente fora | a resiliência quebrando: roda a app com `AGENTE_URL` numa porta morta e exige que a notificação saia com texto padrão. **Nunca chama a API** — nem com credencial |

O validador foi testado contra regressões plantadas de propósito: reintroduzir o
bug do framework e voltar uma URL hardcoded faz as checagens falharem com
arquivo e linha. Um validador que nunca falha não vale nada — se você mudar algo
grande, vale repetir esse teste.

## Regra para os blocos seguintes

**Todo bloco que entrega comportamento novo adiciona sua checagem ao
`validar.py`.** É o que faz o validador continuar valendo algo em novembro. Em
concreto: uma função que levanta `AssertionError` com a explicação, registrada em
`ESTATICAS` ou `VIVAS`.

No bloco 15 isto vira uma suíte pytest de verdade; até lá é um script sem
dependência nova, que roda igual nas duas máquinas.

## Checagem manual por fase

O que o script não alcança:

| Fase | Blocos | Verificar à mão |
|------|--------|-----------------|
| 1 — saneamento | 1–2 | ✅ nada pendente |
| 2 — imóveis | 3–5 | ✅ nada pendente |
| 3 — contratos | 6–9 | ✅ nada pendente |
| 4 — agente | 13–14 | ⚠️ **Pendente e bloqueado:** exige `ANTHROPIC_API_KEY`. Com a chave: (1) na tela `/agente`, perguntar "apartamento de 2 quartos em Maceió até 2000" e conferir que ele chama `buscar_imoveis` com esses filtros e não inventa imóvel; (2) rodar `python apps/app_aviso_vencimento.py` e ver os avisos saírem "redigido por: agente" em vez de texto padrão |
| 5 — frontend | 10–12 | ✅ nada pendente |
| 6 — qualidade | 15–16 | Diagramas refletem o código final; README descreve o que existe |

## Semana 1 (21–27/09) — blocos 1 e 2

**Resultado: 12 checagens, todas passando.** Fase 1 fechada, 5 dias adiantado.

Entregue: bug do hotspot obrigatório corrigido; 17 URLs e 5 caminhos de banco em
env var; `lifespan` nos 5 serviços; headers hop-by-hop filtrados no proxy;
`subir_servicos.py`; `requirements.txt` alinhado ao que está testado;
`.gitattributes` normalizando fim de linha.

Descartado: o path duplicado em `PUBLIC_ROUTES` não era bug (o gateway consome o
primeiro segmento como seletor de serviço). A limpeza do prefixo duplo ficou para
as Fases 2–3, que já renomeiam essas rotas.

## Semana 2 (28/09–04/10) — blocos 3 e 4

**Resultado: 16 checagens, todas passando.** Fase 2 fechada, uma semana adiantado.

Entregue: serviço `catalogo` renomeado para `imoveis` via `git mv` (histórico
preservado); modelo `Imovel` com tipo, endereço, cidade, quartos, banheiros, área e
valor mensal; `definir_disponibilidade(bool)` no lugar do `delta` inteiro; filtros de
cidade, tipo, quartos mínimos e faixa de valor; seeds reescritos com 18 imóveis reais
de Maceió, Recife e João Pessoa.

Verificado à mão, além do validador:

- `seed.py` cadastra os 18 imóveis; `seed_emprestimos.py` insere 42 contratos
  respeitando a restrição de um contrato aberto por imóvel (9 de 18 ficaram ocupados)
- integração empréstimo → imóveis pelo `ImovelClient` booleano: alugar marca o imóvel
  indisponível, devolver libera
- tentar alugar imóvel já alugado devolve `400 Imóvel 'X' já está indisponível` — a
  regra da Fase 3 (um contrato por imóvel) já fica parcialmente imposta pelo serviço
  de imóveis

Antecipado: item 2.6 (interfaces e componentes) saiu junto, porque renomear o serviço
quebra os componentes que o consomem — não dava para deixar o repositório incoerente
entre blocos. Item 2.5 (busca por ISBN) caiu sozinho: o modelo novo não tem ISBN.
Com isso o bloco 5 ficou vazio e vira folga.

Corrigido de passagem: `api.js` chamava `devolver` com PATCH, mas a rota é POST — o
botão de devolução estava quebrado desde o projeto antigo.

## Semana 3 (05–11/10) — blocos 6 a 9

**Resultado: 20 checagens, todas passando.** Fase 3 fechada, duas semanas adiantado.
Com isso o **marco do bloco 9 caiu em 27/09**: o mínimo exigido pelo enunciado
(microsserviços + componentes, funcionando ponta a ponta) está entregue.

Entregue: `emprestimos` virou `contratos`; `Emprestimo` virou `Contrato` com
`inquilino_id`, `imovel_id`, `data_inicio`, `data_fim_prevista`, `data_fim_real` e
`valor_mensal`; prazo de 12 meses; multa de 1/30 do aluguel por dia de atraso; regra de
um contrato aberto por imóvel, imposta no serviço e por índice parcial no banco.

Verificado à mão, além do validador:

- app do framework (`apps/app_contrato.py`) registra contrato pelo Template Method,
  puxa o aluguel do imóvel e dispara a notificação — o argumento de reúso continua de pé
- `seed_contratos.py` insere 42 contratos respeitando a restrição (9 de 18 imóveis
  ocupados); multa do histórico confere na conta (61 dias × R$ 3900/30 = R$ 7930)
- varredura de notificações gera 3 alertas de atraso, cada um com multa proporcional ao
  aluguel do seu imóvel (R$ 10.746,67 / R$ 3.513,33 / R$ 11.160) — que é justamente o
  que a multa fixa de R$ 0,50 não conseguia expressar

Colapsado: os blocos 8 e 9 saíram junto com 6 e 7. Renomear entidade é operação
atômica — mexer nos campos arrasta métodos, regra e cliente. Mesmo padrão do 2.6.
Blocos 5, 8 e 9 ficam como folga.

Nota: um check meu deu falso positivo — procurava a string `MULTA_POR_DIA`, que
aparece no comentário explicando que ela foi substituída. Passou a procurar a
atribuição (`^\s*MULTA_POR_DIA\s*=`).

## Semana 4 (12–18/10) — bloco 10

**Resultado: 23 checagens, todas passando.** O sistema voltou a ser demonstrável.

Entregue: `Catalogo.jsx` substituído por `Imoveis.jsx`, com os filtros estruturados
indo ao backend (não filtragem no navegador), cards de imóvel, formulário de cadastro
e estado de erro. Shell rebrandeado (Sidebar, Login, título da aba).

Verificado no navegador, não só por script:

- login com `admin@alugue.br`, 18 imóveis listados e ordenados por aluguel
- filtro de cidade: 18 → 4 em Recife; somado a tipo=casa → 2. Conferido na aba de rede
  que a requisição sai como `?cidade=Recife&tipo=casa` — quem filtra é o serviço
- cadastro de imóvel novo aparece na lista e respeita os filtros ativos
- com o backend derrubado, aparece "Falha ao carregar" com botão de retentar, e o
  retentar recupera quando os serviços voltam

Duas mentiras de tela removidas, ambas herdadas do projeto antigo:

1. A página caía num array `MOCK` de livros no `.catch` — com o backend fora, você via
   seis livros e concluía que funcionava.
2. O Sidebar tinha a lista de serviços fixa com `ok: true` — seis pontos verdes com
   todos os serviços derrubados. Agora consulta o `/health` do gateway a cada 10s e
   mostra vermelho quando está fora.

Lacuna encontrada: `Dashboard.jsx` não estava em nenhum item do plano e mostra números
inventados (1.247 livros, "Clean Code", "Design Patterns"). Registrado como item 5.7.

Nota sobre o validador: errei duas vezes do mesmo jeito — checagem textual procurando
um nome que aparece no comentário que explica a remoção dele. Agora existe um helper
`sem_comentarios()` que tira comentários antes de procurar, usado nas checagens de
`MULTA_POR_DIA` e de `ok: true`.

## Semana 5 (19–25/10) — bloco 11

**Resultado: 25 checagens, todas passando.** O ciclo de contrato fecha pela interface.

Entregue: `Contratos.jsx` no lugar de `Emprestimos.jsx`. Filtro de status vai ao backend
como query param; tabela com inquilino, imóvel, datas, aluguel, multa e dias em atraso;
formulário que só oferece imóveis sem contrato em aberto; encerramento com feedback de
ação em voo.

Verificado no navegador:

- filtro `?status=atrasado` conferido na aba de rede: 3 contratos
- encerrar o #47 (R$ 5.200, 61 dias de atraso) gerou multa de **R$ 10.573,33**, e o #59
  (R$ 5.400) gerou **R$ 10.980,00** — exatamente 61 × aluguel / 30, calculado pelo serviço
- encerrar devolve o imóvel ao portfólio: os imóveis 5, 11 e 17 reapareceram no
  formulário de novo contrato
- contrato novo (#85) criado pela tela: 2026-10-07 a 2027-10-07, 12 meses exatos

Bug de dados corrigido: o `seed_contratos.py` somava o prazo ao início recente ao
rebaixar um contrato aberto para histórico, o que gerava contratos "encerrados" com
data de saída em 2027 — estado impossível. Agora reposiciona o contrato inteiro no
passado. Conferido: zero contratos com `data_fim_real` no futuro.

Diagnóstico que errei duas vezes antes de acertar: ao clicar em Encerrar, a lista não
mudava. Culpei o HMR do Vite, depois meu próprio código. Nenhum dos dois: a sonda de
2,5s era curta — o refetch faz três chamadas pelo gateway e leva ~3s. O código estava
certo, mas o silêncio de três segundos era problema real de UX, então os botões agora
mostram "Encerrando..." / "Registrando..." e ficam desabilitados durante a ação.

Nota sobre o validador: foi a terceira vez que uma checagem textual minha bateu em
prosa em vez de código (agora o `1/30` escrito no rodapé da tela). A checagem passou a
procurar aritmética com `valor_mensal`, não a menção da regra.

## Semana 6 (26/10–01/11) — bloco 12

**Resultado: 28 checagens, todas passando. Fase 5 fechada.** Nenhuma tela inventa dados,
e o lint do frontend está zerado.

Entregue: `Dashboard`, `Usuarios`, `Notificacoes` e `Recomendacao` reescritos com dados
reais; `Configurador.jsx` removido; menu e rotas ajustados.

Lacunas do plano que apareceram só olhando as telas, agora registradas como 5.7 a 5.9:
o Dashboard, a tela de notificações e a de usuários não estavam em nenhum item da Fase 5
e as três mostravam dados falsos.

Dois achados que valem mais que o bloco:

1. **`localhost` custava 2 segundos por chamada.** O serviço de recomendação levava
   14,6 s e estourava o timeout do gateway. Causa: no Windows `localhost` resolve `::1`
   antes de `127.0.0.1`, e o uvicorn escuta só em IPv4. Medido: 2133 ms com `localhost`
   contra 20 ms com `127.0.0.1`. Trocadas as 17 URLs; o perfil caiu para 0,30 s e a
   recomendação para 0,18 s. Era isto, e não "três chamadas pelo gateway", que fazia o
   botão Encerrar demorar no bloco 11.
2. **A recomendação se esvaziava sozinha.** `PENALIDADE_JA_RECOMENDADO` era 5, igual ao
   score máximo (3 + 2), então todo imóvel recomendado uma vez ficava excluído para
   sempre e a segunda chamada vinha vazia. Com 55 livros passava; com ~9 imóveis
   disponíveis, não. Virou 1: rebaixa em vez de excluir.

Também corrigidos: perfis de usuário ainda eram `aluno` e `bibliotecario` (viraram
`inquilino` e `proprietario`); a descrição do serviço de recomendação ainda dizia
"Recomendação de livros"; e `ImovelRecomendado` não trazia o aluguel — recomendar imóvel
sem dizer o preço não serve para nada.

Colisão de nomes no Windows: separar o hook `useAuth` em `authContext.js` quebrou o
build, porque o Windows não diferencia maiúsculas e o Vite resolveu `./context/AuthContext`
para o arquivo errado. Renomeado para `useAuth.js`. Em Linux teria passado — exatamente o
tipo de divergência entre máquinas que o projeto quer evitar.

## Semana 7 (02–08/11) — bloco 13

**Resultado: 32 checagens, todas passando.** Agente construído, **mas não exercitado
contra o modelo real** — ver a ressalva no fim.

Entregue: serviço `agente` em `:8006`, sétimo processo da composição. Três ferramentas
de leitura (`buscar_imoveis`, `detalhar_imovel`, `listar_contratos`), todas cascas finas
sobre `ComponenteImovelHTTP` e `ComponenteContratoHTTP`. O agente não fala HTTP direto
com nenhum serviço: usa a mesma camada de componentes que as apps do framework.

Decisões que valem registrar:

- **Serviço novo, não substituição.** O plano dizia que `recomendacao` viraria o agente.
  Mantive os dois: o recomendador pontua por histórico de contratos, o agente faz busca
  em linguagem natural. São abordagens diferentes sobre a mesma camada de componentes —
  o contraste ajuda na apresentação, e não destruí código que funciona.
- **Ferramentas só de leitura.** Registrar contrato é ação com efeito colateral e
  dinheiro envolvido; não fica a cargo do modelo nesta fase. Há checagem no validador
  para que uma ferramenta de escrita não apareça sem decisão explícita.
- **O serviço sobe sem credencial.** `/health` responde `ok` e o resto do sistema não
  depende dele; só `POST /agente/perguntar` devolve 503 dizendo o que configurar. Uma
  máquina sem chave não derruba a composição.

Verificado:

- as três ferramentas chamando os serviços de verdade pelos componentes: a busca por
  `cidade=Maceio, tipo=apartamento, valor_max=2000` devolveu 3 imóveis corretos, e o id
  inexistente devolveu erro tratado em vez de estourar
- os schemas das tools gerados a partir da assinatura e do docstring
- o caminho até a API: com uma chave inválida, a chamada chega na Anthropic e volta 401,
  que o serviço mapeia para 503 — ou seja, a requisição é bem formada
- sem credencial: `/agente/status` diz `false` e `perguntar` devolve 503 com instrução

Dois defeitos meus, achados no teste e corrigidos:

1. `/agente/status` dizia `credencial_configurada: true` sem chave nenhuma. O construtor
   do SDK **não** falha sem credencial — ele só reclama ao montar o header. A checagem
   passou a olhar as três fontes que o SDK aceita (`api_key`, `auth_token`, `credentials`).
2. A falta de chave virava **500**, não 503, porque o SDK levanta `TypeError` (não uma
   exceção da família `APIError`) quando não resolve autenticação.

**Ressalva importante:** nada aqui prova que o agente *responde bem*. Que ele escolhe a
ferramenta certa, extrai os filtros da frase e não inventa imóvel só dá para verificar
com uma chave real. Esse teste é o primeiro item do bloco 14.

## Semana 8 (09–15/11) — bloco 14

**Resultado: 36 checagens, todas passando. Fase 4 fechada** — com a ressalva de sempre:
a qualidade da resposta do modelo continua não verificada, por falta de credencial.

Entregue: `POST /agente/redigir-aviso`, `IComponenteAgente` + `ComponenteAgenteHTTP`,
`apps/app_aviso_vencimento.py` e a tela `/agente` com o chat.

A divisão de trabalho é o ponto do bloco:

- quem levanta os contratos é a **App**, pelos componentes (dado é dado);
- quem escreve o texto é o **agente** (prosa é prosa);
- quem envia a notificação é a **App**, pelo componente de notificações.

O modelo não busca dado, não faz conta e não dispara efeito colateral. A regra de multa
continua existindo num lugar só: o serviço de contratos.

Simetria que fecha o argumento de reúso: o agente **consome** componentes (as
ferramentas dele) e **é** um componente (`IComponenteAgente`). Por isso a App orquestra
o agente pelo mesmo Template Method que usa para qualquer outro serviço, sem nenhum
caso especial.

Verificado:

- a App rodando contra os serviços de verdade: achou os 3 contratos vencidos, enviou as
  3 notificações, e o log do framework registrou a execução inteira
- as notificações chegaram nos inquilinos 1, 2 e 3, com o imóvel correto
- **resiliência:** rodando a App com `AGENTE_URL` numa porta morta, o aviso sai mesmo
  assim com texto padrão e a notificação é enviada. O aviso é a função; o agente é o
  acabamento. Essa checagem entrou no validador e nunca chama a API, nem com credencial
- a tela `/agente` mostra o aviso de "sem credencial" e, ao perguntar, exibe o erro real
  em vez de fingir uma resposta

Nota sobre o validador: a checagem "frontend sem vocabulário de biblioteca" acusou a tela
nova por causa do campo `autor` — que ali significa autor da mensagem, não de livro.
Renomeei o campo para `remetente` em vez de afrouxar a checagem: a ambiguidade era real.

**O que continua pendente:** com `ANTHROPIC_API_KEY` definida, falta conferir que o
agente escolhe a ferramenta certa, extrai os filtros da frase e não inventa imóvel; e que
os avisos saem "redigido por: agente". Até lá, a Fase 4 está construída e integrada, mas
não exercitada.

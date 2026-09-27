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
| 4 — agente | 13–14 | O agente responde a uma busca em linguagem natural e chama as tools certas |
| 5 — frontend | 10–12 | Login, listagem, cadastro e contrato pela interface; menu sem itens mortos |
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

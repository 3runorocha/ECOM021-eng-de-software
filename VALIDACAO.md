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
| 2 — imóveis | 3–5 | Swagger em `:8001/docs` mostra os campos de imóvel; filtros de cidade/tipo/quartos retornam o esperado |
| 3 — contratos | 6–9 | Um imóvel com contrato ativo não aceita segundo contrato; multa por atraso confere na conta |
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

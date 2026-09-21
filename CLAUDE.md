# ECOM021 — Engenharia de Software (2026.2)

## O que é este repositório

Projeto da disciplina ECOM021: **sistema usando Microservices e Componentes de Software
[e Agentic AI]**. O enunciado exige obrigatoriamente microsserviços e componentes de
software; Agentic AI é opcional. Linguagem sugerida: Python.

Este repositório **parte do projeto anterior** `3runorocha/tes-rds` (Biblioteca Online,
feito para as disciplinas de Reúso de Software e Tópicos em Engenharia de Software).
O commit inicial é o esqueleto daquele projeto **sem nenhuma adaptação**, de propósito:
o histórico do git passa a ser a evidência do que foi reúso e do que foi construído novo.

**Tema escolhido:** Sistema de Gerenciamento de Aluguel de Apartamentos e Casas.
Motivo: `Emprestimo` e `Contrato de aluguel` têm a mesma estrutura (ator + item +
data início + data fim + multa por atraso), então a adaptação é majoritariamente
renomeação, não remodelagem.

> A adaptação de domínio ainda **não foi feita**. Todo o código atual ainda fala de
> livros/empréstimos. Ver `PLANO_DE_EXECUCAO.md`.

## Arquitetura

Todas as requisições passam por um API Gateway que roteia para os microsserviços.
Cada serviço tem banco SQLite próprio e roda isolado.

| Serviço | Porta | Vira (após adaptação) |
|---------|-------|------------------------|
| API Gateway | 8000 | API Gateway |
| Catálogo | 8001 | Imóveis |
| Usuários | 8002 | Usuários (sem mudança) |
| Empréstimos | 8003 | Contratos |
| Notificações | 8004 | Notificações (sem mudança) |
| Recomendação | 8005 | Serviço de Agente (Agentic AI) |

Stack: Python 3.11+, FastAPI, SQLite, React (Vite), httpx.

## Convenções do código

- **Idioma:** todo o código, nomes e mensagens em português. Manter.
- **Camadas por serviço** (padrão em todos os 5, seguir ao criar qualquer serviço novo):
  `database.py` → `repository.py` → `service.py` → `routes.py` → `main.py`,
  com `models.py` (Pydantic) e `exceptions.py` à parte.
  As dependências são montadas à mão em `main.py` e injetadas via construtor;
  `routes.py` expõe uma factory `criar_router(service)`.
- **Componentes** (`biblioteca/framework/`): contratos `IComponente*` em `interfaces.py`,
  implementações HTTP em `componentes.py`. Todo componente tem ciclo de vida
  `inicializar()` / `finalizar()` e um `get_nome()`.
- **Framework** (`biblioteca/framework/framework.py`): Template Method `executar_operacao()`
  com frozen spots (fluxo fixo) e hotspots (`configurar_componentes`, `executar_logica`,
  `pre_processar`, `pos_processar`, `tratar_erro`, `get_campos_obrigatorios`).
  **Nunca sobrescrever `executar_operacao()`** — é o que caracteriza o reúso via framework.
- **Imports:** os serviços usam imports planos (`from service import ...`), porque cada
  um roda com o uvicorn a partir da sua própria pasta. Não transformar em pacote sem
  ajustar os comandos de execução.

## Como executar

Backend — um comando na raiz sobe os 6 serviços (`--reload` para desenvolvimento,
`Ctrl+C` encerra todos):

```bash
python subir_servicos.py
```

As URLs entre serviços saem de env var com default `localhost`, então numa máquina
só não precisa configurar nada. Para mudar: `.env.example` → `.env` (backend) e
`biblioteca-online/.env.example` → `.env` (frontend, prefixo `VITE_`).

Seed (ordem importa): subir serviços → `python seed.py` → parar serviços →
`python seed_emprestimos.py` → subir de novo.

Frontend: `cd biblioteca-online && npm install && npm run dev` (porta 5173).
Login admin: `admin@biblioteca.br` / `admin123`.

## Estado atual e pendências

Ver `PLANO_DE_EXECUCAO.md` para o detalhamento. Em resumo:

- [x] ~~Bug do framework: `configurar_componentes` definido duas vezes~~ — corrigido
      em 21/09 (bloco 1). `__abstractmethods__` volta a conter os dois hotspots
      obrigatórios e subclasse incompleta é barrada na instanciação.
- [ ] Adaptação do domínio: livros → imóveis, empréstimos → contratos
- [ ] Serviço de agente (Agentic AI) reusando `componentes.py` como camada de tools
- [x] ~~Externalizar as 17 URLs `localhost`~~ — feito em 21/09 (bloco 1), com
      `localhost` mantido como default e `.env.example` documentando as variáveis.
- [x] ~~Script para subir os 6 serviços~~ — `subir_servicos.py` (bloco 2).
- [x] ~~`@app.on_event("startup")` depreciado~~ — trocado por `lifespan` nos 5
      serviços (bloco 2).
- [ ] Testes (não existe nenhum)
- [ ] Docker: **stretch goal**, fora do caminho crítico. Não está instalado em nenhuma
      das máquinas e o enunciado não pede. Ver decisão no fim de `CRONOGRAMA.md`

**Entrega: 09/11/2026. Meta de conclusão: 07/11/2026.** Cronograma em 16 blocos de
3 dias: `CRONOGRAMA.md`. Plano detalhado: `PLANO_DE_EXECUCAO.md`.

## Validação

Ao fim de cada semana, antes de começar o bloco seguinte:

```bash
python validar.py
```

Sobe os 6 serviços com bancos temporários, roda as checagens estáticas e vivas e
sai com código 1 se algo falhar. `--estatico` pula o que precisa subir serviço.

**Regra:** todo bloco que entrega comportamento novo adiciona sua checagem ao
`validar.py`. Detalhes e checklist manual por fase em `VALIDACAO.md`.

## Sobre o sync entre máquinas

Este repositório é usado em duas máquinas. Antes de começar a trabalhar, `git pull`.
Ao terminar, commitar e push — inclusive alterações neste `CLAUDE.md` e no
`PLANO_DE_EXECUCAO.md`, que são o estado compartilhado entre as sessões.

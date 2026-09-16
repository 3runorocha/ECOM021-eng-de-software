# Plano de execução — ECOM021 (2026.2)

Adaptação do esqueleto da Biblioteca Online (`3runorocha/tes-rds`) para um
**Sistema de Gerenciamento de Aluguel de Apartamentos e Casas** usando
Microservices, Componentes de Software e Agentic AI.

**Premissa:** o tema é aluguel de imóveis. Se o tema mudar, as Fases 2 e 3 mudam
inteiras; as Fases 1, 4, 5 e 6 valem para qualquer tema.

**Data de entrega:** a confirmar. O sequenciamento abaixo assume que as fases 1–3
são o mínimo entregável e as 4–6 são o diferencial.

---

## Fase 1 — Saneamento do esqueleto

Independe de tema. Fazer antes de adaptar qualquer coisa.

| # | Ação | Arquivo |
|---|------|---------|
| 1.1 | Remover a definição concreta duplicada de `configurar_componentes` (a segunda, vazia), mantendo só a `@abstractmethod`. Verificar com `FrameworkBiblioteca.__abstractmethods__` — deve conter os dois hotspots obrigatórios | `biblioteca/framework/framework.py` |
| 1.2 | Substituir `@app.on_event("startup")` por `lifespan` (a API está deprecada no FastAPI) | `main.py` dos 5 serviços |
| 1.3 | Corrigir os paths duplicados em `PUBLIC_ROUTES` (`/usuarios/usuarios/login`) | `biblioteca/gateway/config.py` |
| 1.4 | No proxy, não repassar `content-length` / `content-encoding` da resposta upstream — pode corromper a resposta | `biblioteca/gateway/proxy.py` |
| 1.5 | Criar `docker-compose.yml` com os 6 serviços + `Dockerfile` compartilhado. Elimina os 6 terminais manuais e reforça o argumento de microsserviços na apresentação | raiz |

## Fase 2 — Adaptação do domínio: Catálogo → Imóveis

Serviço `catalogo` (8001) vira `imoveis`. **Única mudança estrutural real do projeto:**
um livro tem N exemplares (`quantidade_total` / `quantidade_disponivel`), um imóvel é
único (`disponivel: bool`). Isso muda a assinatura do componente.

| # | Ação | Arquivo |
|---|------|---------|
| 2.1 | Renomear a pasta `services/catalogo` → `services/imoveis` | — |
| 2.2 | `Livro` → `Imovel`: `titulo`, `tipo` (apartamento/casa), `endereco`, `cidade`, `quartos`, `banheiros`, `area_m2`, `valor_mensal`, `disponivel` | `models.py`, `database.py` |
| 2.3 | `atualizar_disponibilidade(livro_id, delta: int)` → `definir_disponibilidade(imovel_id, disponivel: bool)`. Propagar a mudança nos 3 pontos de uso | `service.py`, `routes.py`, `repository.py` |
| 2.4 | Filtros de listagem: `genero`/`autor` → `cidade`, `tipo`, `quartos`, faixa de `valor_mensal` | `repository.py`, `routes.py` |
| 2.5 | Remover a busca por ISBN (era feature opcional da LPS antiga) | `routes.py`, `service.py` |
| 2.6 | Atualizar `IComponenteCatalogo` → `IComponenteImovel` e a implementação HTTP | `framework/interfaces.py`, `framework/componentes.py` |

## Fase 3 — Adaptação do domínio: Empréstimos → Contratos

Serviço `emprestimos` (8003) vira `contratos`. Aqui é quase só renomeação.

| # | De | Para |
|---|----|------|
| 3.1 | `Emprestimo` | `Contrato` |
| 3.2 | `usuario_id`, `livro_id` | `inquilino_id`, `imovel_id` |
| 3.3 | `data_emprestimo`, `data_devolucao_prevista`, `data_devolucao_real` | `data_inicio`, `data_fim_prevista`, `data_fim_real` |
| 3.4 | `PRAZO_DIAS = 14` | `PRAZO_MESES = 12` (data fim = início + 12 meses) |
| 3.5 | `MULTA_POR_DIA = 0.50` | `MULTA_POR_DIA` proporcional ao `valor_mensal` (ex.: 1/30 do aluguel por dia de atraso na desocupação) |
| 3.6 | `registrar_emprestimo` / `registrar_devolucao` | `registrar_contrato` / `encerrar_contrato` |
| 3.7 | `existe_ativo(usuario_id, livro_id)` — "usuário já tem este livro" | `existe_ativo(imovel_id)` — **regra nova:** um imóvel só pode ter um contrato ativo, independente de inquilino |
| 3.8 | `CatalogoClient.atualizar_disponibilidade(id, ±1)` | `ImovelClient.definir_disponibilidade(id, False/True)` |

Arquivos: todos em `services/emprestimos/` → `services/contratos/`.
`usuarios` e `notificacoes` **não mudam** (só o vocabulário dos tipos de notificação).

## Fase 4 — Agentic AI

O serviço `recomendacao` (8005) vira um **serviço de agente**. O encaixe já existe:
`framework/componentes.py` é literalmente uma camada de tools — `buscar_imoveis`,
`registrar_contrato`, `enviar` são assinaturas de ferramenta prontas.

| # | Ação |
|---|------|
| 4.1 | Serviço de agente com a Claude API, expondo os métodos dos `IComponente*` como tools |
| 4.2 | Caso de uso: busca conversacional ("apartamento de 2 quartos em Maceió até R$ 1.800") → o agente chama `buscar_imoveis` com os filtros que extraiu |
| 4.3 | Caso de uso: agente dispara notificação de contrato próximo do vencimento |
| 4.4 | Uma `App` do framework que orquestra o agente, provando que o agente **reusa** o framework em vez de contorná-lo |

> Argumento de arquitetura para a apresentação: o agente não é um apêndice — ele consome
> exatamente a mesma camada de componentes que as apps convencionais.

## Fase 5 — Frontend

| # | Ação | Arquivo |
|---|------|---------|
| 5.1 | Reusar sem mexer: `AuthContext.jsx`, `services/api.js`, `Sidebar.jsx`, `Login.jsx`, CSS | — |
| 5.2 | `Catalogo.jsx` → `Imoveis.jsx` (cards com foto, valor, quartos, cidade) | `src/pages/` |
| 5.3 | `Emprestimos.jsx` → `Contratos.jsx` | `src/pages/` |
| 5.4 | `Recomendacao.jsx` → `Agente.jsx` (interface de chat) | `src/pages/` |
| 5.5 | Remover `Configurador.jsx` (era da LPS da disciplina antiga, fora de escopo aqui) | `src/pages/` |
| 5.6 | Ajustar rotas e itens do menu | `App.jsx`, `Sidebar.jsx` |

## Fase 6 — Qualidade e documentação

| # | Ação |
|---|------|
| 6.1 | Testes: pytest por serviço (camada `service`, com repository fake) + um teste de integração passando pelo gateway |
| 6.2 | Reescrever `seed.py` e `seed_emprestimos.py` para o novo domínio |
| 6.3 | Diagramas: `3_componentes.png` e `5_classes_componentes.png` reusam a estrutura, só relabel. `1_feature_model.png` e `2_ovm.png` são da LPS antiga — descartar |
| 6.4 | Reescrever `README.md`; adaptar `COMO_CRIAR_APP.md`; apagar `COMO_DERIVAR_PRODUTO.md` (LPS, fora de escopo) |
| 6.5 | Adaptar `scrum_biblioteca.md` para o backlog novo |

---

## Ordem sugerida

```
Fase 1  →  Fase 2  →  Fase 3  →  Fase 5  →  Fase 4  →  Fase 6
(sanear)   (imóveis)  (contratos) (telas)   (agente)   (testes/docs)
```

Fases 2 e 3 são acopladas (o cliente HTTP de contratos chama imóveis) — fazer em
sequência, não em paralelo. A Fase 4 vem depois do frontend para que o agente já tenha
uma tela onde ser demonstrado. A Fase 1 é pré-requisito de tudo.

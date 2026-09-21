# Cronograma — ECOM021 (2026.2)

**Início:** 21/09/2026 (segunda) · **Pronto:** 07/11/2026 (sábado) · **Entrega:** 09/11/2026 (segunda)

48 dias = **16 blocos de 3 dias**. Os 2 dias entre "pronto" e "entrega" não são folga
utilizável — o colchão real são os blocos 15 e 16.

Cadência: bloco de 3 dias como unidade de trabalho, semana como sprint para o
registro Scrum (`scrum_biblioteca.md`).

---

## Blocos

| # | Período | Fase | Itens |
|---|---------|------|-------|
| 1 | 21–23/09 | 1 | ✅ **Concluído 21/09.** `configurar_componentes` duplicado corrigido (1.1) · 17 URLs externalizadas em env var + `.env.example` (1.5) · 1.3 verificado e descartado (não era bug) |
| 2 | 24–26/09 | 1 | ✅ **Concluído 21/09.** `lifespan` nos 5 serviços (1.2) · headers hop-by-hop filtrados no proxy (1.4) · `subir_servicos.py` (1.6). Validado: 6 serviços no ar, `/health` geral ok, fluxo registro→login→POST→GET pelo gateway, resposta correta com `--compressed` |
| 3 | 27–29/09 | 2 | Renomear `catalogo` → `imoveis` (2.1) · modelo `Imovel` + schema (2.2) |
| 4 | 30/09–02/10 | 2 | `definir_disponibilidade(bool)` nos 3 pontos de uso (2.3) · filtros cidade/tipo/quartos/valor (2.4) |
| 5 | 03–05/10 | 2 | Remover busca por ISBN (2.5) · `IComponenteImovel` + implementação HTTP (2.6) |
| 6 | 06–08/10 | 3 | `Emprestimo` → `Contrato` (3.1) · `inquilino_id`/`imovel_id` (3.2) · campos de data (3.3) |
| 7 | 09–11/10 | 3 | `PRAZO_MESES = 12` (3.4) · multa proporcional ao `valor_mensal` (3.5) |
| 8 | 12–14/10 | 3 | `registrar_contrato`/`encerrar_contrato` (3.6) · regra nova: um contrato ativo por imóvel (3.7) |
| 9 | 15–17/10 | 3 | `ImovelClient` (3.8) · **integração imóveis ↔ contratos end-to-end pelo gateway** |
| 10 | 18–20/10 | 5 | Reusar shell do frontend (5.1) · `Catalogo.jsx` → `Imoveis.jsx` (5.2) |
| 11 | 21–23/10 | 5 | `Emprestimos.jsx` → `Contratos.jsx` (5.3) |
| 12 | 24–26/10 | 5 | `Agente.jsx` (5.4) · remover `Configurador.jsx` (5.5) · rotas e menu (5.6) |
| 13 | 27–29/10 | 4 | Serviço de agente com Claude API, componentes como tools (4.1) · busca conversacional (4.2) |
| 14 | 30/10–01/11 | 4 | Agente notifica contrato vencendo (4.3) · `App` do framework orquestrando o agente (4.4) |
| 15 | 02–04/11 | 6 | Testes: pytest por serviço + 1 integração (6.1) · reescrever seeds (6.2) |
| 16 | 05–07/11 | 6 | Diagramas (6.3) · README e docs (6.4) · backlog Scrum (6.5) · **stretch: Docker** |

---

## Marcos

| Quando | Estado esperado |
|--------|-----------------|
| Bloco 2 (26/09) | Esqueleto saneado, roda nas duas máquinas por env var |
| Bloco 5 (05/10) | Serviço de imóveis completo |
| Bloco 9 (17/10) | **Backend funcional end-to-end** — mínimo entregável do enunciado |
| Bloco 12 (26/10) | Sistema demonstrável com interface |
| Bloco 14 (01/11) | Agentic AI funcionando (item opcional) |
| Bloco 16 (07/11) | Pronto para entregar |

## Ordem e risco

O obrigatório do enunciado (microsserviços + componentes) fecha no **bloco 9**, com
8 blocos de margem. O agente (opcional) vem nos blocos 13–14, depois do frontend, para
que nasça com tela onde ser demonstrado — e para que, se o tempo apertar, o que fica
de fora seja o opcional, nunca o obrigatório.

Blocos 6–9 são o maior trecho contínuo (Fase 3, 8 itens). São majoritariamente
renomeação, mas é onde um erro passa despercebido por mais tempo: o bloco 9 existe
para validar a integração antes de seguir.

**Decisão sobre Docker:** fora do caminho crítico. O enunciado não pede, e não está
instalado em nenhuma das máquinas (Docker Desktop + WSL2 nas duas). As duas dores que
ele resolveria — subir 6 serviços e portabilidade entre máquinas — são cobertas pelo
script do bloco 2 e pelas env vars do bloco 1. Com as URLs já externalizadas,
containerizar no bloco 16 é meia hora. Se o tempo não sobrar, não se perde nada.

# Plano de execução — ECOM021 (2026.2)

Adaptação do esqueleto da Biblioteca Online (`3runorocha/tes-rds`) para um
**Sistema de Gerenciamento de Aluguel de Apartamentos e Casas** usando
Microservices, Componentes de Software e Agentic AI.

**Premissa:** o tema é aluguel de imóveis. Se o tema mudar, as Fases 2 e 3 mudam
inteiras; as Fases 1, 4, 5 e 6 valem para qualquer tema.

**Data de entrega:** 09/11/2026. Meta de conclusão: 07/11/2026. Ver `CRONOGRAMA.md`
para a distribuição em 16 blocos de 3 dias.

---

## Fase 1 — Saneamento do esqueleto

Independe de tema. Fazer antes de adaptar qualquer coisa.

| # | Ação | Arquivo |
|---|------|---------|
| 1.1 | Remover a definição concreta duplicada de `configurar_componentes` (a segunda, vazia), mantendo só a `@abstractmethod`. Verificar com `FrameworkBiblioteca.__abstractmethods__` — deve conter os dois hotspots obrigatórios | `biblioteca/framework/framework.py` |
| 1.2 | Substituir `@app.on_event("startup")` por `lifespan` (a API está deprecada no FastAPI) | `main.py` dos 5 serviços |
| 1.3 | ~~Corrigir `PUBLIC_ROUTES`~~ — **verificado em 21/09: não é bug.** O path duplicado é coerente: o gateway consome o primeiro segmento como seletor de serviço e repassa o resto, que casa com o `prefix` do router. Limpar o prefixo duplo (`/emprestimos/emprestimos/`) ficou para as Fases 2–3, que já renomeiam essas rotas | — |
| 1.4 | No proxy, não repassar `content-length` / `content-encoding` da resposta upstream — pode corromper a resposta | `biblioteca/gateway/proxy.py` |
| 1.5 | **Externalizar as 17 URLs `localhost` hardcoded** em env var (`os.getenv("IMOVEIS_URL", "http://localhost:8001")`), mantendo o default local. É o que torna o projeto portável entre as duas máquinas, e pré-requisito para containerizar depois | `framework/componentes.py`, `gateway/config.py`, `services/*/main.py`, `seed.py`, `api.js` |
| 1.6 | Script que sobe os 6 serviços de uma vez (resolve os 6 terminais manuais sem precisar de Docker) | raiz |

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
| 2.5 | ✅ Resolvido no bloco 3 — o modelo `Imovel` não tem ISBN, então a rota deixou de existir | — |
| 2.6 | ✅ Antecipado para o bloco 4 — renomear o serviço quebra os componentes, não dava para separar | `framework/interfaces.py`, `framework/componentes.py` |

## Fase 3 — Adaptação do domínio: Empréstimos → Contratos ✅

**Concluída em 27/09** (blocos 6–9 colapsados: renomear entidade é operação atômica).
Serviço `emprestimos` (8003) virou `contratos`.

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
| 4.1 | ✅ **Bloco 13.** Serviço `agente` em :8006. As três ferramentas (`buscar_imoveis`, `detalhar_imovel`, `listar_contratos`) são cascas finas sobre `ComponenteImovelHTTP` e `ComponenteContratoHTTP` — o agente não fala HTTP direto com serviço nenhum. Todas de leitura: registrar contrato envolve dinheiro e não fica a cargo do modelo |
| 4.2 | ⚠️ **Bloco 13, construído mas não exercitado.** `POST /agente/perguntar` monta o loop de ferramentas com o Tool Runner do SDK. O caminho até a API foi validado (uma chave inválida devolve 401 → 503), mas **a qualidade da resposta não foi testada**: falta credencial na máquina |
| 4.3 | Caso de uso: agente dispara notificação de contrato próximo do vencimento |
| 4.4 | Uma `App` do framework que orquestra o agente, provando que o agente **reusa** o framework em vez de contorná-lo |

> Argumento de arquitetura para a apresentação: o agente não é um apêndice — ele consome
> exatamente a mesma camada de componentes que as apps convencionais.

## Fase 5 — Frontend

| # | Ação | Arquivo |
|---|------|---------|
| 5.1 | ✅ **Bloco 10.** `AuthContext.jsx` e `api.js` reusados sem mexer. `Sidebar.jsx` e `Login.jsx` precisaram de rebranding, e o Sidebar trocou a lista fixa `ok: true` por consulta ao `/health` do gateway — mostrava tudo verde com os serviços derrubados | — |
| 5.2 | ✅ **Bloco 10.** `Imoveis.jsx`: filtros de cidade/tipo/quartos/valor enviados ao backend, cards com valor, quartos e situação, formulário de cadastro e estado de erro. Sem foto (não há imagens no projeto) | `src/pages/` |
| 5.3 | ✅ **Bloco 11.** `Contratos.jsx`: filtro de status enviado ao backend, tabela com aluguel/multa/dias de atraso, formulário que só oferece imóveis sem contrato em aberto, encerramento com feedback de ação em voo | `src/pages/` |
| 5.4 | ⚠️ **Parcial (bloco 12).** `Recomendacao.jsx` passou a usar os campos reais do serviço (perfil por tipo e cidade, score sobre 5, aluguel). A interface de chat fica para a Fase 4: batizar a tela de "Agente" antes de o agente existir seria a mesma mentira de tela que esta fase removeu | `src/pages/` |
| 5.5 | ✅ **Bloco 12.** Removido, junto com rota e item de menu | `src/pages/` |
| 5.6 | ✅ **Bloco 12.** | `App.jsx`, `Sidebar.jsx` |
| 5.7 | ✅ **Bloco 12.** `Dashboard.jsx` com números reais: imóveis e disponíveis, contratos em vigor e em atraso, receita mensal contratada, usuários e notificações do usuário logado | `src/pages/Dashboard.jsx` |
| 5.8 | ✅ **Bloco 12.** `Notificacoes.jsx` lia `criado_em` e `canal`, campos que o modelo não tem, e caía em MOCK. Agora usa `data_criacao`/`lida`/`imovel_id`, com ações de marcar lida e rodar varredura | `src/pages/Notificacoes.jsx` |
| 5.9 | ✅ **Bloco 12.** `Usuarios.jsx` tinha MOCK com e-mails `@biblioteca.br` e uma coluna inventada de empréstimos. Agora deriva os contratos em vigor do serviço de contratos | `src/pages/Usuarios.jsx` |

## Fase 6 — Qualidade e documentação

| # | Ação |
|---|------|
| 6.1 | Testes: pytest por serviço (camada `service`, com repository fake) + um teste de integração passando pelo gateway |
| 6.2 | Reescrever `seed.py` e `seed_emprestimos.py` para o novo domínio |
| 6.3 | Diagramas: `3_componentes.png` e `5_classes_componentes.png` reusam a estrutura, só relabel. `1_feature_model.png` e `2_ovm.png` são da LPS antiga — descartar |
| 6.4 | Reescrever `README.md`; adaptar `COMO_CRIAR_APP.md`; apagar `COMO_DERIVAR_PRODUTO.md` (LPS, fora de escopo) |
| 6.5 | Adaptar `scrum_biblioteca.md` para o backlog novo |
| 6.6 | **Stretch:** `docker-compose.yml` + `Dockerfile` compartilhado. Fora do caminho crítico — o enunciado não pede, e as env vars da Fase 1 já resolvem a portabilidade. Só se sobrar tempo |

---

## Ordem sugerida

```
Fase 1  →  Fase 2  →  Fase 3  →  Fase 5  →  Fase 4  →  Fase 6
(sanear)   (imóveis)  (contratos) (telas)   (agente)   (testes/docs)
```

Fases 2 e 3 são acopladas (o cliente HTTP de contratos chama imóveis) — fazer em
sequência, não em paralelo. A Fase 4 vem depois do frontend para que o agente já tenha
uma tela onde ser demonstrado. A Fase 1 é pré-requisito de tudo.

# Scrum — Biblioteca Online

Planejamento ágil do projeto **Biblioteca Online** (Microsserviços + Componentes), aplicável aos dois trabalhos (RDS e TES). A seção de Scrum é compartilhada; apenas a Sprint 4 se divide entre os trabalhos.

## Atores

- **Usuário** — aluno que utiliza a biblioteca (busca, empréstimo, devolução)
- **Bibliotecário** — administrador que gerencia o acervo e os usuários
- **Sistema** — responsável por tarefas automáticas (ex: alertas de prazo)

---

## Product Backlog

Lista priorizada de histórias de usuário, com estimativa em *story points* (escala de Fibonacci) e prioridade.

| ID | Como... | Quero... | Para... | Prioridade | Pts |
|----|---------|----------|---------|------------|-----|
| US01 | bibliotecário | cadastrar livros no acervo | manter o catálogo atualizado | Alta | 3 |
| US02 | usuário | buscar livros por título, autor ou gênero | encontrar o que procuro | Alta | 3 |
| US03 | usuário | buscar um livro por ISBN | localizar a edição exata | Baixa | 2 |
| US04 | sistema | controlar a quantidade disponível de cada exemplar | impedir empréstimo sem estoque | Alta | 2 |
| US05 | usuário | me cadastrar | ter acesso ao sistema | Alta | 2 |
| US06 | usuário | autenticar com email e senha | usar as funcionalidades com segurança | Alta | 3 |
| US07 | bibliotecário | listar os usuários cadastrados | administrar a base | Média | 2 |
| US08 | usuário | pegar um livro emprestado | levá-lo para leitura | Alta | 5 |
| US09 | usuário | devolver um livro | encerrar o empréstimo | Alta | 3 |
| US10 | sistema | calcular multa por atraso na devolução | aplicar a política da biblioteca | Média | 3 |
| US11 | sistema | marcar automaticamente empréstimos vencidos como atrasados | manter o status correto | Média | 2 |
| US12 | usuário | receber alertas de prazo de devolução | evitar atrasos | Média | 3 |
| US13 | sistema | varrer os empréstimos e gerar alertas automaticamente | notificar sem ação manual | Média | 3 |
| US14 | usuário | receber recomendações de livros pelo meu perfil | descobrir novas leituras | Baixa | 5 |
| US15 | sistema | rotear todas as requisições por um API Gateway | ter um ponto de entrada único | Alta | 5 |
| US16 | sistema | validar autenticação no gateway | proteger as rotas | Alta | 3 |
| US17 | desenvolvedor | estruturar o sistema em microsserviços independentes | facilitar manutenção e evolução | Alta | 8 |
| US18 | usuário | acessar o sistema por uma interface web | usar tudo de forma visual | Alta | 5 |
| US19 | bibliotecário | ver o status dos microsserviços em execução | monitorar a saúde do sistema | Baixa | 2 |
| US20 | desenvolvedor | configurar features e derivar novos produtos (LPS) | reusar a base em produtos distintos | Média | 5 |
| US21 | desenvolvedor | reusar um framework com Template Method e hotspots | criar novas aplicações rapidamente | Média | 8 |

**Total:** 21 histórias · 70 story points. As histórias US20 (TES) e US21 (RDS) são as que diferenciam os dois trabalhos.

---

## Organização das Sprints

Quatro sprints de aproximadamente uma semana, alinhadas à ordem de construção do sistema.

| Sprint | Meta da sprint | Histórias | Pts |
|--------|----------------|-----------|-----|
| Sprint 1 | Núcleo de domínio: acervo e usuários | US01, US02, US04, US05, US06, US17 | 23 |
| Sprint 2 | Empréstimos + Gateway | US07, US08, US09, US10, US11, US15, US16 | 23 |
| Sprint 3 | Serviços complementares + Frontend | US03, US12, US13, US14, US18, US19 | 20 |
| Sprint 4 | Reúso (RDS) e Linha de Produto (TES) | US20, US21 | 13 |

---

## Sprint Backlogs detalhados

### Sprint 1 — Núcleo de domínio

Entrega os microsserviços de Catálogo (8001) e Usuários (8002), e fixa a arquitetura de microsserviços. Resultado: cadastrar/buscar livros e registrar/autenticar usuários.

| História | Tarefas técnicas |
|----------|------------------|
| US17 — arquitetura de microsserviços | Definir estrutura de pastas (`services`, `gateway`); padrão FastAPI + SQLite por serviço; configurar CORS; endpoint `/health` por serviço |
| US01 — cadastrar livros | Modelar `Livro`/`LivroCreate` (Pydantic); criar tabela `livros`; rota `POST /livros`; `PATCH /livros/{id}` |
| US02 — buscar livros | Rota `GET /livros` com filtros opcionais de gênero e autor; `GET /livros/{id}` |
| US04 — controlar disponibilidade | Campos `quantidade_total`/`quantidade_disponivel`; rota interna `PATCH /livros/{id}/disponibilidade` |
| US05 — cadastro de usuário | Modelar `UsuarioCreate`; tabela `usuarios`; hash de senha (SHA-256); rota `POST /usuarios/registro` |
| US06 — autenticação | Geração de token de sessão; rota `POST /usuarios/login`; rota interna `POST /usuarios/validar-token` |

### Sprint 2 — Empréstimos + Gateway

Entrega o microsserviço de Empréstimos (8003) com ciclo completo e o API Gateway (8000) com roteamento e autenticação centralizada.

| História | Tarefas técnicas |
|----------|------------------|
| US08 — pegar emprestado | Modelar `Emprestimo`; tabela `emprestimos`; rota `POST /emprestimos`; verificar empréstimo duplicado; decrementar disponibilidade no Catálogo (chamada HTTP) |
| US09 — devolver | Rota `POST /emprestimos/{id}/devolver`; incrementar disponibilidade no Catálogo |
| US10 — multa por atraso | Constantes `PRAZO_DIAS` e `MULTA_POR_DIA`; cálculo de multa na devolução |
| US11 — marcar atrasados | `UPDATE` automático de status vencido para "atrasado" ao listar |
| US07 — listar usuários | Rota `GET /usuarios`; `GET /usuarios/{id}` |
| US15 — API Gateway | Função de proxy reverso; rotas `/{servico}/{path}`; mapa de serviços; `GET /services` |
| US16 — auth no gateway | Middleware de autenticação; rotas públicas (login/registro); validação de token via serviço de Usuários; liberação de OPTIONS (CORS) |

### Sprint 3 — Serviços complementares + Frontend

Entrega Notificações (8004), Recomendação (8005), a busca por ISBN e todo o frontend React.

| História | Tarefas técnicas |
|----------|------------------|
| US12 — alertas de prazo | Modelar `Notificacao`; tabela `notificacoes`; rota `POST /notificacoes`; `GET /notificacoes/usuario/{id}`; marcar como lida |
| US13 — varredura automática | Rota `POST /notificacoes/varredura`; busca empréstimos no serviço 8003; gera alertas de atraso e prazo próximo evitando duplicatas |
| US14 — recomendação | Algoritmo de score por gênero/autor; rota `GET /recomendacao/{id}`; `GET /recomendacao/perfil/{id}`; histórico de recomendações |
| US03 — busca por ISBN | Rota dedicada `GET /livros/isbn/{isbn}` |
| US18 — interface web | Projeto Vite + React; `AuthContext` + tela de Login; páginas (Dashboard, Catálogo, Empréstimos, Usuários, Notificações, Recomendação); `api.js` apontando ao gateway |
| US19 — status dos serviços | Componente Sidebar com indicador de status; painel de microsserviços e portas |

### Sprint 4 — Reúso (RDS) e LPS (TES)

Entrega o framework reusável (RDS) e o configurador de features para derivação de produtos (TES).

| História | Tarefas técnicas |
|----------|------------------|
| US21 — framework reusável (RDS) | Classe abstrata `FrameworkBiblioteca` com Template Method `executar_operacao()`; definir frozen spots e hotspots; interfaces de componente (`IComponente` + 5 especializadas); implementações HTTP; 2 apps de exemplo (`AppEmprestimo`, `AppRecomendacao`); passo a passo de nova app |
| US20 — configurador / LPS (TES) | Feature model e OVM; tela `Configurador` com features obrigatórias/opcionais; regra de dependência (varredura requer notificações); derivação de produto com `config.json` |

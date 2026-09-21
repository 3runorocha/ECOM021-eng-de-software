# Biblioteca Online — Microsserviços e Componentes

Sistema de gerenciamento de biblioteca construído com arquitetura de **microsserviços** (Python + FastAPI) e **frontend** em React. O projeto serve de base para dois trabalhos acadêmicos:

- **RDS (Reúso de Software):** um *framework* reusável baseado no padrão **Template Method**, com *frozen spots* e *hotspots*.
- **TES (Tópicos em Engenharia de Software):** uma **Linha de Produto de Software (LPS)**, com modelo de features, variabilidade (OVM) e configurador para derivação de produtos.

---

## Arquitetura

Todas as requisições passam por um **API Gateway** que roteia para os microsserviços. Cada serviço é independente e possui seu próprio banco SQLite.

| Serviço | Porta | Responsabilidade |
|---------|-------|------------------|
| API Gateway | 8000 | Ponto de entrada único, roteamento e autenticação |
| Catálogo | 8001 | Acervo de livros, busca e disponibilidade |
| Usuários | 8002 | Cadastro e autenticação |
| Empréstimos | 8003 | Empréstimo, devolução e multa |
| Notificações | 8004 | Alertas de prazo (opcional) |
| Recomendação | 8005 | Sugestões por perfil/histórico (opcional) |

**Stack:** Python 3.11+, FastAPI, SQLite, React (Vite), Scrum, GitHub.

---

## Estrutura do repositório

```
rds-tes/
├── biblioteca/                 # Backend (microsserviços)
│   ├── services/
│   │   ├── catalogo/           # :8001
│   │   ├── usuarios/           # :8002
│   │   ├── emprestimos/        # :8003
│   │   ├── notificacoes/       # :8004
│   │   └── recomendacao/       # :8005
│   ├── gateway/                # API Gateway :8000
│   ├── framework/              # Framework reusável (RDS)
│   │   ├── framework.py        # Classe abstrata + Template Method
│   │   ├── interfaces.py       # Contratos dos componentes
│   │   └── componentes.py      # Implementações HTTP
│   ├── apps/                   # Aplicações que reusam o framework (RDS)
│   └── requirements.txt
├── biblioteca-online/          # Frontend React
│   └── src/
│       ├── pages/              # Telas (Dashboard, Catálogo, ..., Configurador)
│       ├── components/         # Sidebar
│       ├── context/            # AuthContext
│       └── services/           # api.js
├── diagramas/                  # Diagramas UML, feature model e OVM
├── COMO_CRIAR_APP.md           # Passo a passo: nova app via framework (RDS)
└── COMO_DERIVAR_PRODUTO.md     # Passo a passo: derivar produto da LPS (TES)
```

---

## Pré-requisitos

- Python 3.11 ou superior
- Node.js 18 ou superior
- npm

---

## Como executar

### 1. Backend

Instale as dependências (a partir da pasta `biblioteca/`):

```bash
cd biblioteca
pip install -r requirements.txt
```

Suba os seis serviços de uma vez, a partir da raiz do repositório:

```bash
python subir_servicos.py
```

Use `--reload` para recarregar ao salvar durante o desenvolvimento. `Ctrl+C`
encerra todos. Se algum serviço morrer, o script derruba o resto e diz qual foi.

<details>
<summary>Alternativa: um terminal por serviço</summary>

```bash
# Catálogo
cd biblioteca/services/catalogo && uvicorn main:app --port 8001 --reload

# Usuários
cd biblioteca/services/usuarios && uvicorn main:app --port 8002 --reload

# Empréstimos
cd biblioteca/services/emprestimos && uvicorn main:app --port 8003 --reload

# Notificações
cd biblioteca/services/notificacoes && uvicorn main:app --port 8004 --reload

# Recomendação
cd biblioteca/services/recomendacao && uvicorn main:app --port 8005 --reload

# API Gateway
cd biblioteca/gateway && uvicorn main:app --port 8000 --reload
```

</details>

As URLs entre serviços vêm de variável de ambiente, com `localhost` como default
— rodar numa máquina só não exige configuração nenhuma. Para mudar, copie
`.env.example` para `.env` (e `biblioteca-online/.env.example` para o frontend).

### 2. Populando o banco de dados

O repositório não inclui dados. Para ter usuários, livros e empréstimos de exemplo, rode os dois scripts de seed na ordem abaixo.

**Passo 1 — seed.py (serviços no ar)**

Cadastra usuários e livros via HTTP. Rode com todos os serviços rodando:

```bash
cd biblioteca
python seed.py
```

Cria 7 usuários e 55 livros. Login de administrador: `admin@biblioteca.br` / `admin123`.

É seguro rodar mais de uma vez — e-mails e ISBNs duplicados são ignorados.

**Passo 2 — seed_emprestimos.py (serviços parados)**

Popula a tabela de empréstimos com acesso direto ao SQLite. **Pare todos os serviços antes de rodar**, a partir da pasta `biblioteca/`:

```bash
cd biblioteca
python seed_emprestimos.py
```

Insere 42 empréstimos (7 usuários × 6 perfis): ativos, atrasados, devolvidos no prazo e devolvidos com multa. Também ajusta a disponibilidade dos livros no catálogo.

Após concluir, suba os serviços novamente.

**Ordem completa:**

```
1. Suba os serviços
2. python seed.py
3. Pare os serviços
4. python seed_emprestimos.py
5. Suba os serviços novamente
```

### 3. Frontend

```bash
cd biblioteca-online
npm install
npm run dev
```

Acesse `http://localhost:5173` e faça login com `admin@biblioteca.br` / `admin123`.

---

## Endpoints úteis

- **Documentação da API (Swagger):** `http://localhost:8000/docs`
- **Status dos serviços:** `http://localhost:8000/health`
- **Lista de microsserviços e portas:** `http://localhost:8000/services`

---

## Documentação adicional

- [`COMO_CRIAR_APP.md`](./COMO_CRIAR_APP.md) — como criar uma nova aplicação reusando o framework (RDS)
- [`COMO_DERIVAR_PRODUTO.md`](./COMO_DERIVAR_PRODUTO.md) — como derivar um novo produto a partir da LPS (TES)
- `diagramas/` — diagrama de classes, diagrama de componentes, feature model e OVM
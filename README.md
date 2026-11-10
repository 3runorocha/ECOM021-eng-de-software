# Aluguel de Imóveis - Microsserviços, Componentes e Agente

Projeto da disciplina **ECOM021 - Engenharia de Software (2026.2)**: sistema de
gerenciamento de aluguel de apartamentos e casas, construído com **microsserviços** e
**componentes de software**, mais um **agente** (item opcional do enunciado).

**Stack:** Python 3.11+, FastAPI, SQLite, React (Vite), API do Gemini ou do Claude.

---

## Origem: este projeto é um caso de reúso

O código parte de [`3runorocha/tes-rds`](https://github.com/3runorocha/tes-rds), o
projeto de Reúso de Software + Tópicos em Engenharia de Software do semestre anterior
(uma biblioteca online). O primeiro commit deste repositório é aquele esqueleto **sem
nenhuma adaptação**, de propósito: o histórico do git mostra o que foi reúso e o que foi
construído para esta disciplina.

O que sobreviveu intacto: o API Gateway, o padrão de camadas dos serviços, o framework
com Template Method e a camada de componentes. O que mudou: o domínio inteiro.

| Antes | Depois |
|---|---|
| `Livro` com N exemplares (`quantidade_disponivel: int`) | `Imovel` único (`disponivel: bool`) |
| `Emprestimo` de 14 dias, multa fixa de R$ 0,50/dia | `Contrato` de 12 meses, multa de 1/30 do aluguel por dia |
| "usuário já tem este livro" | "um contrato em aberto por imóvel", seja qual for o inquilino |

---

## Arquitetura

Sete processos. Tudo entra pelo gateway; cada serviço tem banco próprio.

| Serviço | Porta | Responsabilidade |
|---------|-------|------------------|
| API Gateway | 8000 | Ponto de entrada único, roteamento e autenticação |
| Imóveis | 8001 | Portfólio, busca com filtros e disponibilidade |
| Usuários | 8002 | Cadastro, login e token |
| Contratos | 8003 | Locação, encerramento e multa por atraso |
| Notificações | 8004 | Alertas de prazo e atraso |
| Recomendação | 8005 | Pontuação por histórico de contratos |
| Agente | 8006 | Busca em linguagem natural e redação de avisos |

Diagramas em [`diagramas/`](diagramas/): arquitetura, componentes, framework, ciclo do
contrato e agente.

### Componentes

O enunciado pede microsserviços **e** componentes. Os componentes são uma camada
explícita em [`biblioteca/framework/`](biblioteca/framework/): interfaces `IComponente*`
com ciclo de vida (`inicializar`/`finalizar`) e implementações HTTP. Quem consome não
monta requisição - chama um método.

A mesma camada serve as aplicações do framework **e** as ferramentas do agente. Ver
[`diagramas/2_componentes.md`](diagramas/2_componentes.md).

---

## Como executar

### Pré-requisitos

Python 3.11+, Node.js 18+, npm.

```bash
pip install -r biblioteca/requirements.txt
cd biblioteca-online && npm install && cd ..
```

### 1. Backend

Um comando sobe os sete processos. `--reload` recarrega ao salvar; `Ctrl+C` encerra
todos. Se algum serviço morrer, o script derruba o resto e diz qual foi.

```bash
python subir_servicos.py
```

### 2. Dados de exemplo

O repositório não inclui bancos. Rode os dois seeds **nesta ordem**:

```bash
# 1. com os serviços no ar
cd biblioteca && python seed.py
```

Cria 7 usuários e 18 imóveis em Maceió, Recife e João Pessoa.
Login de administrador: `admin@alugue.br` / `admin123`.

O cadastro público não cria administrador: só o **primeiro** usuário do banco pode
ser admin, e o seed cadastra o admin primeiro.

> **Banco criado antes de 16/10 não faz login.** O hash de senha mudou (PBKDF2 com
> sal, no lugar de SHA-256 com segredo fixo). Apague os `.db` em
> `biblioteca/services/*/` e rode os dois seeds de novo.

Usuários duplicados são ignorados. **Imóveis não**: diferente do livro, que tinha ISBN,
imóvel não tem chave única de negócio - rodar de novo duplica o portfólio. Apague
`biblioteca/services/imoveis/imoveis.db` para recomeçar.

```bash
# 2. com os serviços PARADOS
cd biblioteca && python seed_contratos.py
```

Insere 42 contratos (7 inquilinos × 6 perfis): ativos, atrasados e encerrados, estes com
multa proporcional ao aluguel de cada imóvel. Como um imóvel é único, no máximo um
contrato fica em aberto por imóvel - quando os livres acabam, os demais entram como
histórico encerrado.

Depois suba os serviços de novo.

### 3. Frontend

```bash
cd biblioteca-online && npm run dev
```

Acesse `http://localhost:5173`.

### 4. Agente (opcional)

O serviço de agente sobe e responde `/health` sem credencial, mas as rotas que pensam
devolvem 503 explicando o que falta. Ele funciona com o **Gemini** (Google, com nível
gratuito) ou com o **Claude** (Anthropic, pago à parte); basta uma das chaves.

1. Gere uma chave gratuita do Gemini em https://aistudio.google.com ("Get API key").
2. Copie `.env.example` para `.env`, na raiz, e preencha `GEMINI_API_KEY=` com a chave.
3. Suba os serviços de novo com `python subir_servicos.py`: ele lê o `.env`.

Com as duas chaves, vale o Gemini; para usar o Claude, defina `AGENTE_PROVEDOR=anthropic`.
A tela do Agente mostra qual provedor e qual modelo estão em uso.

Nenhum outro serviço depende dele. Não comite a chave: o `.env` está no `.gitignore`.

---

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest                  # unidade: rápidos, sem serviço no ar
python -m pytest -m integracao    # pelo gateway; exige os serviços no ar
```

Os de unidade exercitam a camada de serviço com repositórios fake - sem SQLite e sem
rede. Os de integração são pulados, não falham, quando os serviços não estão no ar.

Para validar o projeto inteiro de uma vez (invariantes + suíte + integração com bancos
temporários):

```bash
python validar.py
```

As checagens estão descritas em [`VALIDACAO.md`](VALIDACAO.md). O validador sobe os
serviços com bancos temporários, então não suja os dados de desenvolvimento.

### Testes de ponta a ponta

A pasta [`e2e/`](e2e/) testa o sistema pelo navegador, com Playwright: 29 cenários em
Gherkin ([`e2e/casos.feature`](e2e/casos.feature)), um teste para cada. Exigem os
serviços e o frontend no ar, com os dados de exemplo do `seed.py` e do
`seed_contratos.py`. Os bancos são copiados antes e restaurados a cada caso.

```bash
cd e2e
pip install -r requirements.txt
python -m playwright install chromium
python -m pytest test_prototipo.py -v
```

Passam 27 de 29: o CT26 e o CT29 expõem dois defeitos conhecidos (recomendação sem
restrição por usuário e menu lateral no celular). O passo a passo para Windows, a
gravação da demonstração narrada e o relatório HTML estão no
[`e2e/README.md`](e2e/README.md).

---

## Configuração

As URLs entre serviços saem de variável de ambiente, com default local - rodar numa
máquina só não exige configuração nenhuma. Para mudar, copie `.env.example` para `.env`
(e `biblioteca-online/.env.example` para o frontend).

> Use `127.0.0.1`, nunca `localhost`. No Windows, `localhost` resolve `::1` antes de
> `127.0.0.1` e o uvicorn escuta só em IPv4: medido **2133 ms por chamada contra 20 ms**.

---

## Estrutura

```
ECOM021-eng-de-software/
├── biblioteca/                  # Backend
│   ├── services/
│   │   ├── imoveis/             # :8001
│   │   ├── usuarios/            # :8002
│   │   ├── contratos/           # :8003
│   │   ├── notificacoes/        # :8004
│   │   ├── recomendacao/        # :8005
│   │   └── agente/              # :8006
│   ├── gateway/                 # :8000
│   ├── framework/               # Template Method + componentes
│   ├── apps/                    # Aplicações que reusam o framework
│   ├── seed.py, seed_contratos.py
│   └── requirements.txt
├── biblioteca-online/           # Frontend React
├── diagramas/                   # Mermaid
├── tests/                       # pytest
├── e2e/                         # testes pelo navegador (Playwright)
├── subir_servicos.py            # sobe os 7 processos
├── validar.py                   # checagens do projeto inteiro
├── CRONOGRAMA.md                # blocos de 3 dias, 21/09 a 07/11
├── PLANO_DE_EXECUCAO.md         # o plano, item a item
├── VALIDACAO.md                 # o que cada checagem pega, semana a semana
└── COMO_CRIAR_APP.md            # criar uma app reusando o framework
```

> As pastas `biblioteca/` e `biblioteca-online/` mantêm o nome herdado do projeto
> original. Renomeá-las quebraria a rastreabilidade do reúso no histórico do git, que é
> justamente o que este trabalho quer mostrar.

---

## Endpoints úteis

- **Swagger agregado:** `http://127.0.0.1:8000/docs`
- **Saúde dos serviços:** `http://127.0.0.1:8000/health`
- **Portas e descrições:** `http://127.0.0.1:8000/services`

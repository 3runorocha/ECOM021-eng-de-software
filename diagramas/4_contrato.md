# 4 — Ciclo de um contrato

A operação central do sistema, e o lugar onde dois serviços precisam concordar sobre um
mesmo fato: o imóvel está ocupado ou não.

## Assinatura

```mermaid
sequenceDiagram
    actor U as Navegador
    participant G as Gateway :8000
    participant C as Contratos :8003
    participant I as Imóveis :8001

    U->>G: POST /contratos/contratos/
    G->>G: valida token
    G->>C: encaminha

    C->>I: GET /imoveis/{id}
    I-->>C: imóvel + valor_mensal
    Note over C: não existe? 400

    C->>C: existe contrato aberto<br/>para este imóvel?
    Note over C: existe? 400

    C->>I: PATCH disponibilidade = false
    I-->>C: ok

    C->>C: INSERT contrato<br/>(índice parcial único)

    alt INSERT falhou (corrida)
        C->>I: PATCH disponibilidade = true
        Note over C,I: compensação: imóvel não<br/>pode ficar preso sem contrato
        C-->>G: 400
    else sucesso
        C-->>G: 201 contrato ativo
    end
    G-->>U: resposta
```

### A regra, imposta em dois níveis

Um imóvel só aceita **um contrato em aberto**, seja qual for o inquilino — diferente do
acervo de livros, onde a checagem era por (usuário, livro) porque havia vários
exemplares do mesmo título.

1. **No serviço:** `existe_aberto(imovel_id)` antes de qualquer escrita.
2. **No banco:** índice parcial único sobre `imovel_id` onde o status está em aberto.

O segundo nível existe porque o primeiro tem janela: duas requisições simultâneas podem
passar pela checagem antes de qualquer uma inserir. Aí o índice barra a segunda, e a
compensação devolve a disponibilidade.

## Encerramento e multa

```mermaid
sequenceDiagram
    actor U as Navegador
    participant G as Gateway :8000
    participant C as Contratos :8003
    participant I as Imóveis :8001

    U->>G: POST /contratos/{id}/encerrar
    G->>C: encaminha
    Note over C: já encerrado? 400
    C->>C: multa = dias_atraso × valor_mensal / 30
    C->>I: PATCH disponibilidade = true
    C->>C: UPDATE status = encerrado
    C-->>G: 201 contrato encerrado + multa
    G-->>U: resposta
```

A multa é **proporcional ao aluguel contratado**, não um valor fixo: um dia de atraso
custa 1/30 do aluguel. O contrato grava o `valor_mensal` na assinatura, porque o aluguel
do imóvel pode mudar depois e a multa é sobre o que foi acordado.

Exemplo real do sistema, com 61 dias de atraso:

| Imóvel | Aluguel | Multa |
|---|---|---|
| Studio em Casa Forte | R$ 1.700 | R$ 3.513,33 |
| Cobertura na Pajuçara | R$ 5.200 | R$ 10.746,67 |

A regra mora só no serviço de contratos. A tela mostra os dias em atraso, mas não
calcula dinheiro — há checagem no validador para isso não se duplicar.

Arquivo: [`services/contratos/service.py`](../biblioteca/services/contratos/service.py) ·
Testes: [`tests/test_contratos.py`](../tests/test_contratos.py)

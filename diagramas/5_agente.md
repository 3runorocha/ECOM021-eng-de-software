# 5 - Agente (Agentic AI)

O item opcional do enunciado. A decisão de projeto que o sustenta: **o agente usa a
mesma camada de componentes que as aplicações convencionais**, em vez de falar HTTP por
conta própria. Sem isso ele seria um apêndice pendurado ao lado do sistema.

## Simetria: consome componentes e é um componente

```mermaid
flowchart LR
    subgraph app["App do framework"]
        aviso["AppAvisoVencimento"]
    end

    subgraph camada["Camada de componentes"]
        ci["ComponenteImovelHTTP"]
        cc["ComponenteContratoHTTP"]
        cn["ComponenteNotificacaoHTTP"]
        ca["ComponenteAgenteHTTP"]
    end

    subgraph agente["Serviço de agente :8006"]
        tools["ferramentas.py"]
        loop["Tool Runner"]
    end

    aviso --> cc & ci & ca & cn
    ca --> loop
    loop --> tools
    tools --> ci & cc

    style ca fill:#dbeafe,stroke:#1d4ed8
    style tools fill:#dbeafe,stroke:#1d4ed8
```

A caixa azul aparece dos dois lados: o agente **é** `ComponenteAgenteHTTP` para quem o
orquestra, e **usa** `ComponenteImovelHTTP`/`ComponenteContratoHTTP` como ferramentas.
Por isso a app o trata como qualquer outro serviço, sem caso especial.

## Busca conversacional

```mermaid
sequenceDiagram
    actor U as Usuário
    participant A as Agente :8006
    participant M as Claude
    participant C as Componentes
    participant I as Imóveis :8001

    U->>A: "apartamento de 2 quartos<br/>em Maceió até R$ 2.000"
    A->>M: pergunta + 3 ferramentas
    M-->>A: buscar_imoveis(cidade, tipo,<br/>quartos_min, valor_max)
    A->>C: componente.buscar_imoveis(filtros)
    C->>I: GET /imoveis/?cidade=...
    I-->>C: imóveis
    C-->>A: resultado
    A->>M: resultado da ferramenta
    M-->>A: resposta em português
    A-->>U: resposta + ferramentas chamadas
```

As três ferramentas são **só de leitura**: `buscar_imoveis`, `detalhar_imovel`,
`listar_contratos`. Registrar contrato é ação com efeito colateral e dinheiro
envolvido - não fica a cargo do modelo. Há checagem no validador.

## Aviso de vencimento: quem faz o quê

```mermaid
flowchart TD
    A["App: levanta contratos vencendo<br/>pelos componentes"]:::codigo
    B["Agente: redige o texto<br/>a partir dos fatos recebidos"]:::modelo
    C["App: envia a notificação<br/>pelo componente"]:::codigo
    D["Agente fora do ar<br/>ou sem credencial"]:::falha
    E["App: usa texto padrão"]:::codigo

    A --> B --> C
    A -.-> D -.-> E --> C

    classDef codigo fill:#e5e7eb,stroke:#6b7280,color:#111
    classDef modelo fill:#dbeafe,stroke:#1d4ed8,color:#111
    classDef falha fill:#fee2e2,stroke:#991b1b,color:#111
```

Dado é dado, prosa é prosa. O modelo não busca dado, não faz conta e não dispara efeito
colateral - por isso a regra de multa continua existindo num lugar só.

**O aviso é a função; o agente é o acabamento.** Com o agente fora, a app cai num texto
padrão e segue avisando. Há checagem viva que roda a app com `AGENTE_URL` numa porta
morta e exige que a notificação saia mesmo assim.

## Estado

Construído e integrado, **mas não exercitado contra o modelo real** - falta
`ANTHROPIC_API_KEY` na máquina de desenvolvimento. O que foi verificado sem chave: as
ferramentas chamando os serviços de verdade, os schemas gerados dos docstrings, e o
caminho até a API (uma chave inválida chega na Anthropic e volta 401).

Arquivos: [`services/agente/`](../biblioteca/services/agente/) ·
[`apps/app_aviso_vencimento.py`](../biblioteca/apps/app_aviso_vencimento.py)

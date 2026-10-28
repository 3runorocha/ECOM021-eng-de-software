# 3 - Framework reusável (Template Method)

Herdado do trabalho de Reúso de Software e mantido intacto na migração de domínio: o
framework não menciona imóvel nem contrato em lugar nenhum. O que mudou foram as apps.

`executar_operacao()` fixa a sequência. A aplicação preenche só os pontos de adaptação.

```mermaid
classDiagram
    class FrameworkBiblioteca {
        <<abstract>>
        -_componentes dict
        -_log list
        +executar_operacao(contexto) Any
        +registrar_componente(nome, componente)
        +get_componente(nome) IComponente
        +get_log() list
        -_inicializar_componentes()
        -_validar_pre_condicoes(contexto)
        -_registrar_log(contexto, resultado, duracao)
        -_finalizar_componentes()
        +configurar_componentes()*
        +executar_logica(contexto)*
        +pre_processar(contexto)
        +pos_processar(contexto, resultado)
        +tratar_erro(contexto, erro) dict
        +get_campos_obrigatorios() list
    }

    class AppContrato {
        +configurar_componentes()
        +executar_logica(contexto)
        +pre_processar(contexto)
        +pos_processar(contexto, resultado)
    }

    class AppRecomendacao {
        +configurar_componentes()
        +executar_logica(contexto)
    }

    class AppAvisoVencimento {
        +configurar_componentes()
        +executar_logica(contexto)
        +pre_processar(contexto)
        +pos_processar(contexto, resultado)
    }

    FrameworkBiblioteca <|-- AppContrato
    FrameworkBiblioteca <|-- AppRecomendacao
    FrameworkBiblioteca <|-- AppAvisoVencimento
```

## Frozen spots e hotspots

```mermaid
flowchart TD
    A["1. inicializar componentes"]:::frozen
    B["2. validar pré-condições"]:::frozen
    C["3. pre_processar()"]:::hot
    D["4. executar_logica()"]:::hot
    E["5. pos_processar()"]:::hot
    F["tratar_erro()"]:::hot
    G["6. registrar log"]:::frozen
    H["7. finalizar componentes"]:::frozen

    A --> B --> C --> D --> E --> G --> H
    B -. "campo faltando" .-> F
    C -. "exceção" .-> F
    D -. "exceção" .-> F
    F --> G

    classDef frozen fill:#e5e7eb,stroke:#6b7280,color:#111
    classDef hot fill:#dbeafe,stroke:#1d4ed8,color:#111
```

Cinza é do framework e não se toca. Azul é o que a aplicação implementa.

Dois hotspots são **obrigatórios** (`configurar_componentes` e `executar_logica`): são
`@abstractmethod`, então uma subclasse que esqueça um deles não instancia.

> Isso valia no projeto original só na intenção: `configurar_componentes` estava
> declarado duas vezes, e a segunda definição - concreta e vazia - apagava a primeira.
> `__abstractmethods__` continha apenas `executar_logica`, e uma app sem componentes
> rodava até falhar mais tarde em `get_componente()`. Corrigido no bloco 1, com teste.

## Garantias

- A ordem é do framework. Nenhuma app sobrescreve `executar_operacao()` - há teste.
- Componentes são finalizados **mesmo quando a lógica estoura**.
- Toda execução vira entrada de log com duração e status; o log **não guarda senha**.

Arquivo: [`framework/framework.py`](../biblioteca/framework/framework.py) ·
Testes: [`tests/test_framework.py`](../tests/test_framework.py)

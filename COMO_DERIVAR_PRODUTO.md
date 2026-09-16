# Como derivar um novo produto a partir da LPS (TES)

Este guia mostra como construir um produto específico a partir da Linha de Produto de Software (LPS) da Biblioteca Online, selecionando features e gerando uma configuração.

## Conceito

Numa LPS não se constrói cada sistema do zero. Existe uma **base comum** (features obrigatórias, presentes em todo produto) e um conjunto de **features opcionais**. Cada combinação de features opcionais gera um **produto diferente**. O ato de escolher as features e gerar a configuração final chama-se **derivação de produto**.

## Features da linha

### Obrigatórias (presentes em todo produto)

| Feature | Camada |
|---------|--------|
| Catálogo (busca no acervo) | Serviço |
| Usuários (autenticação por token) | Serviço |
| Empréstimos (com multa por atraso) | Serviço |
| API Gateway | Serviço |

### Opcionais (definem a variabilidade)

| Feature | Camada | Depende de |
|---------|--------|-----------|
| Notificações | Serviço | — |
| Recomendação | Serviço | — |
| Busca por ISBN | Componente | — |
| Varredura automática | Componente | Notificações |

> **Restrição de dependência:** a varredura automática só pode ser ativada se o serviço de Notificações estiver presente no produto.

## Passo 1 — Abrir o configurador

No frontend (`http://localhost:5173`), acesse a tela **Configurador** pelo menu lateral. As features obrigatórias aparecem marcadas e travadas; as opcionais ficam disponíveis para seleção.

## Passo 2 — Selecionar as features opcionais

Marque as features desejadas. Exemplos de produtos possíveis:

**Produto A — Biblioteca Completa**
- Notificações ✓
- Recomendação ✓
- Busca por ISBN ✓
- Varredura automática ✓

**Produto B — Biblioteca Básica**
- Notificações ✗
- Recomendação ✗
- Busca por ISBN ✗
- Varredura automática ✗ (indisponível, pois depende de Notificações)

**Produto C — Biblioteca com Descoberta**
- Notificações ✗
- Recomendação ✓
- Busca por ISBN ✓
- Varredura automática ✗

## Passo 3 — Derivar o produto

Clique em **Derivar produto**. O configurador valida as dependências e gera:

1. A lista de **microsserviços que sobem** para aquele produto
2. Os **componentes opcionais ativos**
3. Um arquivo de configuração `config.json` que descreve o produto derivado

Exemplo de `config.json` para o Produto C:

```json
{
  "notificacoes": false,
  "recomendacao": true,
  "busca_isbn": true,
  "varredura": false
}
```

## Passo 4 — Materializar o produto

A configuração derivada define quais serviços iniciar. Na prática, isso se traduz em subir apenas os microsserviços correspondentes às features ativas:

- Produto A (completo): sobe os 6 serviços (8000 a 8005)
- Produto B (básico): sobe apenas Gateway, Catálogo, Usuários e Empréstimos (8000, 8001, 8002, 8003)
- Produto C: sobe Gateway, Catálogo, Usuários, Empréstimos e Recomendação (8000, 8001, 8002, 8003, 8005)

## Resumo

| Etapa | Resultado |
|-------|-----------|
| Selecionar features | Define a variabilidade do produto |
| Validar dependências | Garante combinações válidas (ex: varredura exige notificações) |
| Derivar | Gera o `config.json` e a lista de serviços |
| Materializar | Sobe apenas os serviços das features escolhidas |

A base comum permanece idêntica entre todos os produtos; o que muda é o conjunto de features opcionais ativadas. Essa é a essência da reutilização em uma Linha de Produto de Software.

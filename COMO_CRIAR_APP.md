# Como criar uma aplicação reusando o framework

Guia para construir uma aplicação nova aproveitando o `FrameworkBiblioteca`:
você implementa só os **hotspots**, sem tocar nos **frozen spots**.

## O conceito

`executar_operacao()` é um **Template Method**: ele fixa a sequência de qualquer
operação do sistema.

```
1. [FROZEN] inicializar componentes
2. [FROZEN] validar pré-condições
3. [HOT]    pre_processar()        ← você implementa
4. [HOT]    executar_logica()      ← você implementa (obrigatório)
5. [HOT]    pos_processar()        ← você implementa
6. [FROZEN] registrar log
7. [FROZEN] finalizar componentes
   [HOT]    tratar_erro()          ← você implementa (em caso de falha)
```

Os passos **FROZEN** são garantidos pelo framework, inclusive quando sua lógica estoura:
os componentes são finalizados e o log é registrado de qualquer jeito.

Diagrama: [`diagramas/3_framework.md`](diagramas/3_framework.md).

## Componentes disponíveis

Em [`biblioteca/framework/componentes.py`](biblioteca/framework/componentes.py):

| Componente | Principais métodos |
|---|---|
| `ComponenteImovelHTTP` | `buscar_imoveis(filtros)`, `cadastrar_imovel(dados)`, `definir_disponibilidade(id, bool)` |
| `ComponenteUsuarioHTTP` | `registrar(dados)`, `autenticar(email, senha)`, `buscar_usuario(id)` |
| `ComponenteContratoHTTP` | `registrar_contrato(inquilino_id, imovel_id)`, `encerrar_contrato(id)`, `listar_contratos(inquilino_id=None)` |
| `ComponenteNotificacaoHTTP` | `enviar(usuario_id, tipo, mensagem, imovel_id)`, `listar(usuario_id)` |
| `ComponenteRecomendacaoHTTP` | `recomendar(usuario_id, limite)`, `obter_perfil(usuario_id)` |
| `ComponenteAgenteHTTP` | `perguntar(texto, inquilino_id)`, `redigir_aviso(fatos)` |

Você nunca monta requisição HTTP: chama o método. Se precisar de uma capacidade que não
existe, acrescente ao contrato (`IComponente*`) **e** à implementação - não contorne a
camada.

## Passo 1 - Estender o framework

Crie um arquivo em `biblioteca/apps/`, por exemplo `app_minha_operacao.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'framework'))

from framework import FrameworkBiblioteca
from componentes import ComponenteImovelHTTP, ComponenteNotificacaoHTTP


class AppMinhaOperacao(FrameworkBiblioteca):
    pass
```

## Passo 2 - Os dois hotspots obrigatórios

`configurar_componentes()` e `executar_logica()` são `@abstractmethod`: sem eles a
classe nem instancia.

```python
class AppMinhaOperacao(FrameworkBiblioteca):

    def configurar_componentes(self):
        self.registrar_componente("imoveis", ComponenteImovelHTTP())
        self.registrar_componente("notificacoes", ComponenteNotificacaoHTTP())

    def executar_logica(self, contexto):
        imoveis = self.get_componente("imoveis")
        return imoveis.buscar_imoveis({"cidade": contexto["cidade"]})
```

## Passo 3 - Os hotspots opcionais

Têm comportamento padrão; sobrescreva só o que precisar.

```python
    def get_campos_obrigatorios(self):
        # Validado antes de qualquer lógica rodar.
        return ["cidade"]

    def pre_processar(self, contexto):
        contexto["cidade"] = contexto["cidade"].strip().title()

    def pos_processar(self, contexto, resultado):
        notificacoes = self.get_componente("notificacoes")
        notificacoes.enviar(
            usuario_id=contexto["usuario_id"],
            tipo="busca",
            mensagem=f"{len(resultado)} imóveis encontrados em {contexto['cidade']}",
        )

    def tratar_erro(self, contexto, erro):
        return {"erro": True, "mensagem": "Falha na busca", "detalhe": str(erro)}
```

## Passo 4 - Executar

```python
if __name__ == "__main__":
    app = AppMinhaOperacao()
    resultado = app.executar_operacao({"cidade": "maceió", "usuario_id": 1})
    print(resultado)
    for entrada in app.get_log():
        print(entrada)
```

## Resumo

| Você faz | O framework garante |
|----------|---------------------|
| Implementa `configurar_componentes()` | Inicializa e finaliza os componentes |
| Implementa `executar_logica()` | Valida pré-condições e registra o log |
| (Opcional) sobrescreve os demais hotspots | Mantém a ordem imutável, mesmo com erro |

Nenhuma aplicação reescreve `executar_operacao()` nem os métodos internos - é
exatamente isso que caracteriza o reúso via framework, e há teste que verifica.

## Usando o agente numa app

O agente é um componente como qualquer outro. Vale a divisão de trabalho que a
`AppAvisoVencimento` usa:

- quem **levanta dado** é a app, pelos componentes;
- quem **escreve texto** é o agente;
- quem **dispara efeito colateral** é a app.

Assim o modelo não busca dado, não faz conta e não grava nada - e a regra de negócio
continua existindo num lugar só.

```python
    def executar_logica(self, contexto):
        agente = self.get_componente("agente")
        try:
            return agente.redigir_aviso(contexto["fatos"])
        except Exception:
            return self._texto_padrao(contexto)   # o agente é o acabamento
```

## Exemplos no repositório

- [`app_contrato.py`](biblioteca/apps/app_contrato.py) - registra contrato e notifica
- [`app_recomendacao.py`](biblioteca/apps/app_recomendacao.py) - perfil e recomendações, com fallback
- [`app_aviso_vencimento.py`](biblioteca/apps/app_aviso_vencimento.py) - orquestra o agente

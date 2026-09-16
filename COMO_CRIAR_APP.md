# Como criar uma nova aplicação reusando o framework (RDS)

Este guia mostra como construir uma nova aplicação reaproveitando o framework `FrameworkBiblioteca`, implementando apenas os **hotspots** sem tocar nos **frozen spots**.

## Conceito

O framework define um **Template Method** chamado `executar_operacao()`, que fixa a sequência de execução de qualquer operação da biblioteca:

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

Os passos **FROZEN** são fixos e garantidos pelo framework. Você só preenche os **HOTSPOTS** — os pontos de adaptação.

## Passo 1 — Criar a classe da aplicação

Crie um arquivo em `biblioteca/apps/`, por exemplo `app_minha_operacao.py`, e estenda a classe abstrata:

```python
from framework import FrameworkBiblioteca
from componentes import ComponenteCatalogoHTTP, ComponenteUsuarioHTTP


class AppMinhaOperacao(FrameworkBiblioteca):
    pass
```

## Passo 2 — Implementar os hotspots obrigatórios

Toda aplicação precisa implementar pelo menos dois hotspots: `configurar_componentes()` e `executar_logica()`.

```python
class AppMinhaOperacao(FrameworkBiblioteca):

    def configurar_componentes(self):
        # Registra os componentes que esta app vai usar
        self.registrar_componente("catalogo", ComponenteCatalogoHTTP())
        self.registrar_componente("usuarios", ComponenteUsuarioHTTP())

    def executar_logica(self, contexto):
        # A operação de negócio em si
        catalogo = self.get_componente("catalogo")
        return catalogo.buscar_livros({"genero": contexto["genero"]})
```

## Passo 3 — Implementar os hotspots opcionais (se precisar)

Os demais hotspots têm comportamento padrão e só são sobrescritos quando necessário:

```python
    def get_campos_obrigatorios(self):
        # Garante que o contexto traga os dados necessários
        return ["genero"]

    def pre_processar(self, contexto):
        # Ex: normalizar dados de entrada
        contexto["genero"] = contexto["genero"].strip().capitalize()

    def pos_processar(self, contexto, resultado):
        # Ex: registrar métrica, disparar evento
        print(f"{len(resultado)} livros encontrados")

    def tratar_erro(self, contexto, erro):
        # Ex: tratamento personalizado de falha
        return {"erro": True, "mensagem": "Falha na busca", "detalhe": str(erro)}
```

## Passo 4 — Executar a aplicação

```python
if __name__ == "__main__":
    app = AppMinhaOperacao()
    resultado = app.executar_operacao({"genero": "tecnologia"})
    print(resultado)
```

Ao chamar `executar_operacao()`, o framework executa toda a sequência fixa automaticamente, invocando seus hotspots nos momentos certos.

## Resumo

| Você faz | O framework garante |
|----------|---------------------|
| Implementa `configurar_componentes()` | Inicializa e finaliza os componentes |
| Implementa `executar_logica()` | Valida pré-condições e registra log |
| (Opcional) sobrescreve os demais hotspots | Mantém a ordem de execução imutável |

Repare que nenhuma aplicação reescreve `executar_operacao()` nem os métodos internos (`_inicializar_componentes`, `_validar_pre_condicoes`, etc.). É exatamente isso que caracteriza o reúso via framework: o fluxo é herdado e fixo, só os pontos de extensão variam.

As aplicações de exemplo `app_emprestimo.py` e `app_recomendacao.py` (na pasta `apps/`) seguem esse mesmo padrão.

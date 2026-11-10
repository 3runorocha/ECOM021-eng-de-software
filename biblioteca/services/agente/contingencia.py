"""Busca de contingencia: quando o modelo nao responde dentro do prazo.

Tira os filtros da propria pergunta com regras simples (cidade, tipo, numero
de quartos e teto de aluguel) e chama a mesma ferramenta de busca do agente.
Os imoveis sao os de verdade, do servico de imoveis; o que fica mais simples e
a leitura da frase, e a resposta diz isso. Nao e uma resposta inventada.
"""
import re
import unicodedata

CIDADES = {"maceio": "Maceio", "recife": "Recife", "joao pessoa": "Joao Pessoa"}
TIPOS = {
    "casa": ("casa", "casas"),
    "apartamento": ("apartamento", "apartamentos", "apto", "ap", "studio", "estudio",
                    "kitnet", "kitnete", "quitinete", "flat", "cobertura"),
}


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold()


def _valor(numero: str, mil: str) -> float:
    valor = float(numero.replace(".", "").replace(",", "."))
    return valor * 1000 if mil else valor


def extrair_filtros(pergunta: str) -> dict:
    """Os filtros que da para tirar da frase sem modelo. Vazio se nada bater."""
    texto = _normalizar(pergunta)
    palavras = set(re.findall(r"[a-z]+", texto))
    filtros = {}

    for chave, cidade in CIDADES.items():
        if re.search(rf"\b{chave}\b", texto):
            filtros["cidade"] = cidade
            break

    for tipo, sinonimos in TIPOS.items():
        if palavras & set(sinonimos):
            filtros["tipo"] = tipo
            break

    quartos = re.search(r"(\d+)\s*(?:quartos?|qtos?|dormitorios?)", texto)
    if quartos:
        filtros["quartos_min"] = int(quartos.group(1))

    teto = re.search(r"(?:ate|maximo|max|no maximo)\s*(?:r\$\s*)?(\d[\d.,]*)\s*(mil|k)?", texto)
    if teto:
        filtros["valor_max"] = _valor(teto.group(1), teto.group(2))

    return filtros


def descrever(filtros: dict) -> str:
    partes = []
    if "tipo" in filtros:
        partes.append(filtros["tipo"])
    if "cidade" in filtros:
        partes.append(f"em {filtros['cidade']}")
    if "quartos_min" in filtros:
        partes.append(f"com {filtros['quartos_min']}+ quarto(s)")
    if "valor_max" in filtros:
        partes.append(f"até R$ {filtros['valor_max']:,.0f}".replace(",", "."))
    return ", ".join(partes) or "todos os imóveis disponíveis"

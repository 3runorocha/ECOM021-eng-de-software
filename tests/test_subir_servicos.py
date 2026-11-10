"""subir_servicos.py: o .env da raiz chega aos serviços, sem biblioteca extra."""
import importlib.util

from conftest import RAIZ

especificacao = importlib.util.spec_from_file_location("subir_servicos", RAIZ / "subir_servicos.py")
subir = importlib.util.module_from_spec(especificacao)
especificacao.loader.exec_module(subir)


def test_le_chave_e_valor_ignorando_comentarios_e_vazios(tmp_path):
    arquivo = tmp_path / ".env"
    arquivo.write_text(
        "# comentário do exemplo\n"
        "\n"
        "GEMINI_API_KEY=abc123\n"
        "ANTHROPIC_API_KEY=\n"
        "AGENTE_PROVEDOR = \"gemini\"\n"
        "linha sem igual\n",
        encoding="utf-8",
    )
    assert subir.ler_env(arquivo) == {"GEMINI_API_KEY": "abc123", "AGENTE_PROVEDOR": "gemini"}


def test_sem_arquivo_nao_ha_nada_a_ler(tmp_path):
    assert subir.ler_env(tmp_path / ".env") == {}

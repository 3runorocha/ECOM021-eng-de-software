"""Hash de senha e token do serviço de usuários."""
import pytest

from conftest import carregar

seguranca, excecoes = carregar("usuarios", "security", "exceptions")

PasswordHasher = seguranca.PasswordHasher
TokenService = seguranca.TokenService
TokenInvalido = excecoes.TokenInvalido

SEGREDO = "segredo-de-teste"


def test_hash_e_deterministico():
    hasher = PasswordHasher(SEGREDO)
    assert hasher.hash("senha123") == hasher.hash("senha123")


def test_hash_nao_devolve_a_senha():
    assert "senha123" not in PasswordHasher(SEGREDO).hash("senha123")


def test_hash_muda_com_o_segredo():
    assert PasswordHasher("a").hash("senha123") != PasswordHasher("b").hash("senha123")


def test_senhas_diferentes_geram_hashes_diferentes():
    hasher = PasswordHasher(SEGREDO)
    assert hasher.hash("senha123") != hasher.hash("senha124")


def test_token_gerado_valida_e_devolve_quem_e():
    servico = TokenService(SEGREDO)
    token = servico.gerar(7, "pedro@alugue.br")
    assert servico.validar(token) == {"usuario_id": 7, "email": "pedro@alugue.br"}


def test_dois_tokens_do_mesmo_usuario_sao_diferentes():
    """Tem nonce: token repetido seria mais fácil de reusar se vazasse."""
    servico = TokenService(SEGREDO)
    assert servico.gerar(1, "a@b.c") != servico.gerar(1, "a@b.c")


def test_token_adulterado_e_recusado():
    servico = TokenService(SEGREDO)
    token = servico.gerar(1, "ana@alugue.br")
    # Troca o id de usuário mantendo o resto: a assinatura não fecha mais.
    partes = token.split(":")
    partes[0] = "999"
    with pytest.raises(TokenInvalido):
        servico.validar(":".join(partes))


def test_token_de_outro_segredo_e_recusado():
    token = TokenService("segredo-a").gerar(1, "a@b.c")
    with pytest.raises(TokenInvalido):
        TokenService("segredo-b").validar(token)


def test_token_expirado_e_recusado():
    expirado = TokenService(SEGREDO, horas_validade=-1).gerar(1, "a@b.c")
    with pytest.raises(TokenInvalido):
        TokenService(SEGREDO).validar(expirado)


@pytest.mark.parametrize("lixo", ["", "nada", "a:b:c", "1:a@b.c:x:y:z"])
def test_token_malformado_e_recusado(lixo):
    with pytest.raises(TokenInvalido):
        TokenService(SEGREDO).validar(lixo)


def test_validade_do_token_confere_com_o_relogio_real():
    """O campo expires precisa ser verdadeiro em UTC, não só consistente.

    Com datetime.utcnow() (ingênuo) o .timestamp() interpretava o valor como
    hora local: aqui, UTC-3, um token de 8h declarava 11h.
    """
    from datetime import datetime, timezone

    token = TokenService(SEGREDO, horas_validade=8).gerar(1, "a@b.c")
    expires = int(token.split(":")[2])
    agora = int(datetime.now(timezone.utc).timestamp())
    horas = (expires - agora) / 3600
    assert 7.9 < horas < 8.1, f"token declara {horas:.1f}h de validade, não 8h"

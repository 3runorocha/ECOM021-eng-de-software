"""Hash de senha e token do serviço de usuários."""
import pytest

from conftest import carregar

seguranca, excecoes = carregar("usuarios", "security", "exceptions")

PasswordHasher = seguranca.PasswordHasher
TokenService = seguranca.TokenService
TokenInvalido = excecoes.TokenInvalido

SEGREDO = "segredo-de-teste"


def test_senha_certa_verifica():
    hasher = PasswordHasher()
    assert hasher.verificar("senha123", hasher.hash("senha123"))


def test_senha_errada_nao_verifica():
    hasher = PasswordHasher()
    assert not hasher.verificar("senha124", hasher.hash("senha123"))


def test_hash_nao_devolve_a_senha():
    assert "senha123" not in PasswordHasher().hash("senha123")


def test_mesma_senha_gera_hashes_diferentes():
    """Sal por usuário: dois usuários com a mesma senha não têm o mesmo hash,
    então vazar o banco não revela quem compartilha senha nem permite tabela
    pré-calculada."""
    hasher = PasswordHasher()
    assert hasher.hash("senha123") != hasher.hash("senha123")


def test_hash_nao_depende_de_segredo_no_codigo():
    """O hash antigo era sha256(senha + segredo), com o segredo no repositório.
    O de agora só depende da senha e do sal guardado junto."""
    guardado = PasswordHasher().hash("senha123")
    algoritmo, iteracoes, sal, derivada = guardado.split("$")
    assert algoritmo == "pbkdf2_sha256"
    assert int(iteracoes) >= 600_000
    assert len(sal) == 32
    assert PasswordHasher().verificar("senha123", guardado)


@pytest.mark.parametrize("guardado", ["", "lixo", "a$b$c", "md5$1$00$ff", None])
def test_hash_guardado_invalido_nao_verifica(guardado):
    assert not PasswordHasher().verificar("senha123", guardado)


def test_token_exige_segredo():
    with pytest.raises(ValueError):
        TokenService("")


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

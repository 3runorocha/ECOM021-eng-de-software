"""Popula a tabela de contratos com acesso direto ao SQLite.

Rodar com os servicos PARADOS, depois do seed.py.

Um imovel so pode ter um contrato em aberto -- regra imposta pelo servico e
tambem por indice parcial no banco. Este script respeita a restricao: quando os
imoveis livres acabam, os contratos restantes entram como historico encerrado.
"""
import calendar
import os
import sqlite3
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
DB_CONTRATOS = os.path.join(BASE, "services", "contratos", "contratos.db")
DB_IMOVEIS = os.path.join(BASE, "services", "imoveis", "imoveis.db")

PRAZO_MESES = 12
DIAS_BASE_MULTA = 30
HOJE = date.today()


def somar_meses(inicio, meses):
    total = inicio.month - 1 + meses
    ano = inicio.year + total // 12
    mes = total % 12 + 1
    dia = min(inicio.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def iso(d):
    return d.isoformat()


def conectar(caminho):
    if not os.path.exists(caminho):
        raise FileNotFoundError(
            f"Banco nao encontrado: {caminho}\n"
            "Suba os servicos ao menos uma vez para criar os bancos, "
            "depois pare-os e rode este script."
        )
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    return conn


def main():
    imo = conectar(DB_IMOVEIS)
    con = conectar(DB_CONTRATOS)

    imoveis = [dict(r) for r in imo.execute(
        "SELECT id, valor_mensal FROM imoveis ORDER BY id"
    ).fetchall()]
    if not imoveis:
        print("Nenhum imovel cadastrado. Rode o seed.py primeiro.")
        return

    inquilinos_ids = list(range(1, 8))

    con.execute("DELETE FROM contratos")
    con.commit()
    imo.execute("UPDATE imoveis SET disponivel = 1")
    imo.commit()

    # Offsets em meses a partir de hoje. Um contrato dura PRAZO_MESES, entao
    # "atrasado" e um que comecou ha mais de 12 meses e nao foi encerrado.
    perfis = [
        {"inicio": -36, "tipo": "encerrado",       "saida": -23},
        {"inicio": -30, "tipo": "encerrado_multa", "saida": -16},
        {"inicio": -3,  "tipo": "ativo"},
        {"inicio": -1,  "tipo": "ativo"},
        {"inicio": -14, "tipo": "atrasado"},
        {"inicio": -60, "tipo": "encerrado",       "saida": -48},
    ]

    ocupados = set()
    total = 0
    multa_total = 0.0
    idx = 0
    n_imoveis = len(imoveis)

    for uid in inquilinos_ids:
        for p in perfis:
            imovel = imoveis[idx % n_imoveis]
            idx += 1
            imovel_id = imovel["id"]
            valor_mensal = imovel["valor_mensal"]
            tipo = p["tipo"]

            # Imovel ja com contrato aberto nao recebe outro: vira historico.
            # Reposiciona o contrato inteiro no passado, em vez de somar o prazo
            # ao inicio recente -- isso deixava "encerrado" com data de saida no
            # futuro, que e estado impossivel.
            if tipo in ("ativo", "atrasado") and imovel_id in ocupados:
                tipo = "encerrado"
                p = {"inicio": -(PRAZO_MESES + 2), "tipo": "encerrado", "saida": -2}

            data_inicio = somar_meses(HOJE, p["inicio"])
            data_prev = somar_meses(data_inicio, PRAZO_MESES)

            if tipo in ("encerrado", "encerrado_multa"):
                data_saida = somar_meses(HOJE, p["saida"])
                dias_atraso = max(0, (data_saida - data_prev).days)
                multa = round(dias_atraso * (valor_mensal / DIAS_BASE_MULTA), 2)
                status, fim_real = "encerrado", iso(data_saida)
                multa_total += multa
            elif tipo == "atrasado":
                status, multa, fim_real = "atrasado", 0.0, None
            else:
                status, multa, fim_real = "ativo", 0.0, None

            con.execute(
                """INSERT INTO contratos
                   (inquilino_id, imovel_id, data_inicio, data_fim_prevista,
                    data_fim_real, valor_mensal, status, multa)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid, imovel_id, iso(data_inicio), iso(data_prev),
                 fim_real, valor_mensal, status, multa),
            )
            total += 1

            if status in ("ativo", "atrasado"):
                ocupados.add(imovel_id)
                imo.execute(
                    "UPDATE imoveis SET disponivel = 0 WHERE id = ?", (imovel_id,)
                )

    con.commit()
    imo.commit()

    por_status = {r["status"]: r["n"] for r in con.execute(
        "SELECT status, COUNT(*) n FROM contratos GROUP BY status"
    ).fetchall()}
    con.close()
    imo.close()

    print(f"Inseridos {total} contratos ({len(inquilinos_ids)} inquilinos x {len(perfis)} perfis).")
    print("Por status:", por_status)
    print(f"{len(ocupados)} de {n_imoveis} imoveis com contrato em aberto (indisponiveis).")
    print(f"Multa acumulada no historico: R$ {multa_total:.2f}")
    print("\nSuba os servicos novamente para ver os dados no frontend.")


if __name__ == "__main__":
    main()

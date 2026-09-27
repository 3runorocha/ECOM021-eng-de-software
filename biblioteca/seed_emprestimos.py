"""Popula a tabela de emprestimos com acesso direto ao SQLite.

Rodar com os servicos PARADOS, depois do seed.py.

Nota sobre a Fase 2: um imovel e unico, diferente do acervo de livros, que
tinha N exemplares. Entao no maximo um contrato em aberto por imovel -- e a
regra que o servico de contratos vai passar a impor na Fase 3 (item 3.7). Este
script ja respeita a restricao: quando os imoveis livres acabam, os contratos
restantes entram como historico encerrado em vez de ficarem em aberto.

Os nomes de tabela e coluna (emprestimos, livro_id) seguem os do servico atual
e serao renomeados junto com ele na Fase 3.
"""
import os
import sqlite3
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DB_EMPRESTIMOS = os.path.join(BASE, "services", "emprestimos", "emprestimos.db")
DB_IMOVEIS = os.path.join(BASE, "services", "imoveis", "imoveis.db")

PRAZO_DIAS = 14
MULTA_POR_DIA = 0.50
HOJE = date.today()


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
    emp = conectar(DB_EMPRESTIMOS)

    imoveis = [dict(r) for r in imo.execute(
        "SELECT id FROM imoveis ORDER BY id"
    ).fetchall()]
    if not imoveis:
        print("Nenhum imovel cadastrado. Rode o seed.py primeiro.")
        return

    usuarios_ids = list(range(1, 8))

    emp.execute("DELETE FROM emprestimos")
    emp.commit()
    imo.execute("UPDATE imoveis SET disponivel = 1")
    imo.commit()

    perfis = [
        {"inicio_offset": -30, "tipo": "encerrado",       "fim_offset": -20},
        {"inicio_offset": -40, "tipo": "encerrado_multa", "fim_offset": -18},
        {"inicio_offset": -5,  "tipo": "ativo"},
        {"inicio_offset": -2,  "tipo": "ativo"},
        {"inicio_offset": -25, "tipo": "atrasado"},
        {"inicio_offset": -60, "tipo": "encerrado",       "fim_offset": -50},
    ]

    ocupados = set()
    total = 0
    idx = 0
    n_imoveis = len(imoveis)

    for uid in usuarios_ids:
        for p in perfis:
            imovel_id = imoveis[idx % n_imoveis]["id"]
            idx += 1
            tipo = p["tipo"]

            # Um imovel ja com contrato em aberto nao pode receber outro.
            if tipo in ("ativo", "atrasado") and imovel_id in ocupados:
                tipo = "encerrado"
                p = {**p, "fim_offset": p["inicio_offset"] + PRAZO_DIAS}

            data_inicio = HOJE + timedelta(days=p["inicio_offset"])
            data_prev = data_inicio + timedelta(days=PRAZO_DIAS)

            if tipo == "encerrado":
                data_real = HOJE + timedelta(days=p["fim_offset"])
                status, multa, fim_real = "devolvido", 0.0, iso(data_real)
            elif tipo == "encerrado_multa":
                data_real = HOJE + timedelta(days=p["fim_offset"])
                atraso = max(0, (data_real - data_prev).days)
                status = "devolvido"
                multa = round(atraso * MULTA_POR_DIA, 2)
                fim_real = iso(data_real)
            elif tipo == "atrasado":
                status, multa, fim_real = "atrasado", 0.0, None
            else:
                status, multa, fim_real = "ativo", 0.0, None

            emp.execute(
                """INSERT INTO emprestimos
                   (usuario_id, livro_id, data_emprestimo, data_devolucao_prevista,
                    data_devolucao_real, status, multa)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (uid, imovel_id, iso(data_inicio), iso(data_prev), fim_real, status, multa),
            )
            total += 1

            if status in ("ativo", "atrasado"):
                ocupados.add(imovel_id)
                imo.execute(
                    "UPDATE imoveis SET disponivel = 0 WHERE id = ?", (imovel_id,)
                )

    emp.commit()
    imo.commit()

    por_status = {r["status"]: r["n"] for r in emp.execute(
        "SELECT status, COUNT(*) n FROM emprestimos GROUP BY status"
    ).fetchall()}
    emp.close()
    imo.close()

    print(f"Inseridos {total} contratos ({len(usuarios_ids)} usuarios x {len(perfis)} perfis).")
    print("Por status:", por_status)
    print(f"{len(ocupados)} de {n_imoveis} imoveis ficaram indisponiveis (contrato em aberto).")
    print("\nSuba os servicos novamente para ver os dados no frontend.")


if __name__ == "__main__":
    main()

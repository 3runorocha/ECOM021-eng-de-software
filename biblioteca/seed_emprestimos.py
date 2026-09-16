import os
import sqlite3
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DB_EMPRESTIMOS = os.path.join(BASE, "services", "emprestimos", "emprestimos.db")
DB_CATALOGO    = os.path.join(BASE, "services", "catalogo", "catalogo.db")

PRAZO_DIAS = 14
MULTA_POR_DIA = 0.50
HOJE = date.today()


def iso(d):
    return d.isoformat()


def conectar(caminho):
    if not os.path.exists(caminho):
        raise FileNotFoundError(
            f"Banco nao encontrado: {caminho}\n"
            "Suba os servicos ao menos uma vez para criar os bancos, depois pare-os e rode este script."
        )
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    return conn


def main():
    cat = conectar(DB_CATALOGO)
    emp = conectar(DB_EMPRESTIMOS)

    livros = [dict(r) for r in cat.execute(
        "SELECT id, quantidade_disponivel FROM livros ORDER BY id"
    ).fetchall()]
    if not livros:
        print("Nenhum livro no catalogo. Rode o seed.py primeiro.")
        return

    usuarios_ids = list(range(1, 8))

    emp.execute("DELETE FROM emprestimos")
    emp.commit()

    cat.execute("UPDATE livros SET quantidade_disponivel = quantidade_total")
    cat.commit()

    perfis = [
        {"emp_offset": -30, "tipo": "devolvido", "dev_offset": -20},
        {"emp_offset": -40, "tipo": "devolvido_multa", "dev_offset": -18},
        {"emp_offset": -5,  "tipo": "ativo"},
        {"emp_offset": -2,  "tipo": "ativo"},
        {"emp_offset": -25, "tipo": "atrasado"},
        {"emp_offset": -60, "tipo": "devolvido", "dev_offset": -50},
    ]

    total = 0
    livro_idx = 0
    n_livros = len(livros)

    for uid in usuarios_ids:
        for p in perfis:
            livro = livros[livro_idx % n_livros]
            livro_idx += 1
            livro_id = livro["id"]

            data_emp = HOJE + timedelta(days=p["emp_offset"])
            data_prev = data_emp + timedelta(days=PRAZO_DIAS)

            if p["tipo"] == "devolvido":
                data_real = HOJE + timedelta(days=p["dev_offset"])
                status = "devolvido"
                multa = 0.0
                dev_real = iso(data_real)
            elif p["tipo"] == "devolvido_multa":
                data_real = HOJE + timedelta(days=p["dev_offset"])
                atraso = max(0, (data_real - data_prev).days)
                multa = round(atraso * MULTA_POR_DIA, 2)
                status = "devolvido"
                dev_real = iso(data_real)
            elif p["tipo"] == "atrasado":
                status = "atrasado"
                multa = 0.0
                dev_real = None
            else:
                status = "ativo"
                multa = 0.0
                dev_real = None

            emp.execute(
                """INSERT INTO emprestimos
                   (usuario_id, livro_id, data_emprestimo, data_devolucao_prevista,
                    data_devolucao_real, status, multa)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (uid, livro_id, iso(data_emp), iso(data_prev), dev_real, status, multa),
            )
            total += 1

            if status in ("ativo", "atrasado"):
                cat.execute(
                    "UPDATE livros SET quantidade_disponivel = MAX(0, quantidade_disponivel - 1) WHERE id = ?",
                    (livro_id,),
                )

    emp.commit()
    cat.commit()

    por_status = {r["status"]: r["n"] for r in emp.execute(
        "SELECT status, COUNT(*) n FROM emprestimos GROUP BY status"
    ).fetchall()}
    emp.close()
    cat.close()

    print(f"Inseridos {total} emprestimos ({len(usuarios_ids)} usuarios x {len(perfis)}).")
    print("Por status:", por_status)
    print("Disponibilidade do catalogo ajustada para os emprestimos em aberto.")
    print("\nSuba os servicos novamente para ver os dados no frontend.")


if __name__ == "__main__":
    main()
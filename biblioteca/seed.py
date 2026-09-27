import os

import httpx

USUARIOS_URL = os.getenv("USUARIOS_URL", "http://localhost:8002")
IMOVEIS_URL = os.getenv("IMOVEIS_URL", "http://localhost:8001")

USUARIOS = [
    {"nome": "Admin",         "email": "admin@alugue.br",   "senha": "admin123", "tipo": "admin"},
    {"nome": "Ana Souza",     "email": "ana@alugue.br",     "senha": "senha123", "tipo": "aluno"},
    {"nome": "Carlos Lima",   "email": "carlos@alugue.br",  "senha": "senha123", "tipo": "aluno"},
    {"nome": "Joao Melo",     "email": "joao@alugue.br",    "senha": "senha123", "tipo": "aluno"},
    {"nome": "Maria Silva",   "email": "maria@alugue.br",   "senha": "senha123", "tipo": "aluno"},
    {"nome": "Beatriz Rocha", "email": "beatriz@alugue.br", "senha": "senha123", "tipo": "bibliotecario"},
    {"nome": "Pedro Alves",   "email": "pedro@alugue.br",   "senha": "senha123", "tipo": "aluno"},
]

IMOVEIS = [
    {"titulo": "Apartamento na Ponta Verde",  "tipo": "apartamento", "endereco": "Av. Alvaro Otacilio, 1200",     "cidade": "Maceio",      "quartos": 2, "banheiros": 2, "area_m2": 72.0,  "valor_mensal": 2400.0},
    {"titulo": "Studio na Jatiuca",           "tipo": "apartamento", "endereco": "Rua Jangadeiros Alagoanos, 88", "cidade": "Maceio",      "quartos": 1, "banheiros": 1, "area_m2": 38.0,  "valor_mensal": 1500.0},
    {"titulo": "Casa no Farol",               "tipo": "casa",        "endereco": "Rua Dr. Jose Neto, 340",        "cidade": "Maceio",      "quartos": 3, "banheiros": 2, "area_m2": 140.0, "valor_mensal": 3100.0},
    {"titulo": "Apartamento no Pinheiro",     "tipo": "apartamento", "endereco": "Rua Epaminondas Gracindo, 45",  "cidade": "Maceio",      "quartos": 2, "banheiros": 1, "area_m2": 65.0,  "valor_mensal": 1800.0},
    {"titulo": "Cobertura na Pajucara",       "tipo": "apartamento", "endereco": "Av. Dr. Antonio Gouveia, 910",  "cidade": "Maceio",      "quartos": 3, "banheiros": 3, "area_m2": 155.0, "valor_mensal": 5200.0},
    {"titulo": "Casa no Tabuleiro",           "tipo": "casa",        "endereco": "Rua Sao Bento, 77",             "cidade": "Maceio",      "quartos": 3, "banheiros": 2, "area_m2": 110.0, "valor_mensal": 1900.0},
    {"titulo": "Apartamento no Serraria",     "tipo": "apartamento", "endereco": "Av. Menino Marcelo, 2300",      "cidade": "Maceio",      "quartos": 2, "banheiros": 2, "area_m2": 68.0,  "valor_mensal": 2100.0},
    {"titulo": "Kitnet no Centro",            "tipo": "apartamento", "endereco": "Rua do Comercio, 15",           "cidade": "Maceio",      "quartos": 1, "banheiros": 1, "area_m2": 28.0,  "valor_mensal": 950.0},
    {"titulo": "Casa em Boa Viagem",          "tipo": "casa",        "endereco": "Rua Bruno Veloso, 500",         "cidade": "Recife",      "quartos": 4, "banheiros": 3, "area_m2": 210.0, "valor_mensal": 6800.0},
    {"titulo": "Apartamento em Boa Viagem",   "tipo": "apartamento", "endereco": "Av. Conselheiro Aguiar, 3400",  "cidade": "Recife",      "quartos": 3, "banheiros": 2, "area_m2": 95.0,  "valor_mensal": 3600.0},
    {"titulo": "Studio em Casa Forte",        "tipo": "apartamento", "endereco": "Rua das Pernambucanas, 120",    "cidade": "Recife",      "quartos": 1, "banheiros": 1, "area_m2": 42.0,  "valor_mensal": 1700.0},
    {"titulo": "Casa nas Gracas",             "tipo": "casa",        "endereco": "Rua da Hora, 260",              "cidade": "Recife",      "quartos": 3, "banheiros": 2, "area_m2": 150.0, "valor_mensal": 4200.0},
    {"titulo": "Apartamento em Manaira",      "tipo": "apartamento", "endereco": "Av. Gov. Flavio Ribeiro, 700",  "cidade": "Joao Pessoa", "quartos": 2, "banheiros": 2, "area_m2": 70.0,  "valor_mensal": 2300.0},
    {"titulo": "Casa no Bessa",               "tipo": "casa",        "endereco": "Rua Silvino Chaves, 40",        "cidade": "Joao Pessoa", "quartos": 3, "banheiros": 3, "area_m2": 165.0, "valor_mensal": 3900.0},
    {"titulo": "Apartamento no Cabo Branco",  "tipo": "apartamento", "endereco": "Av. Cabo Branco, 1500",         "cidade": "Joao Pessoa", "quartos": 2, "banheiros": 1, "area_m2": 58.0,  "valor_mensal": 2000.0},
    {"titulo": "Kitnet em Jaguaribe",         "tipo": "apartamento", "endereco": "Rua Almeida Barreto, 210",      "cidade": "Joao Pessoa", "quartos": 1, "banheiros": 1, "area_m2": 32.0,  "valor_mensal": 880.0},
    {"titulo": "Casa em Intermares",          "tipo": "casa",        "endereco": "Av. Praia de Intermares, 33",   "cidade": "Joao Pessoa", "quartos": 4, "banheiros": 3, "area_m2": 190.0, "valor_mensal": 5400.0},
    {"titulo": "Apartamento nos Bancarios",   "tipo": "apartamento", "endereco": "Rua Josefa Taveira, 800",       "cidade": "Joao Pessoa", "quartos": 2, "banheiros": 1, "area_m2": 55.0,  "valor_mensal": 1400.0},
]


def main():
    with httpx.Client(timeout=10.0) as client:
        print("== Cadastrando usuarios ==")
        for u in USUARIOS:
            try:
                r = client.post(f"{USUARIOS_URL}/usuarios/registro", json=u)
                if r.status_code == 201:
                    print(f"  + {u['nome']} ({u['email']})")
                else:
                    print(f"  . {u['email']} ja existe ou invalido (status {r.status_code})")
            except httpx.RequestError:
                print(f"  ! falha ao conectar em {USUARIOS_URL} - o servico de Usuarios esta no ar?")
                return

        print(f"\n== Cadastrando imoveis ({len(IMOVEIS)}) ==")
        ok = 0
        for i in IMOVEIS:
            try:
                r = client.post(f"{IMOVEIS_URL}/imoveis/", json=i)
                if r.status_code == 201:
                    ok += 1
                    print(f"  + {i['titulo']} ({i['cidade']}, R$ {i['valor_mensal']:.0f})")
                else:
                    print(f"  . {i['titulo']} invalido (status {r.status_code})")
            except httpx.RequestError:
                print(f"  ! falha ao conectar em {IMOVEIS_URL} - o servico de Imoveis esta no ar?")
                return

    print(f"\nConcluido. {ok} imoveis cadastrados. Login admin: admin@alugue.br / admin123")
    print("Atencao: imovel nao tem chave unica de negocio (o livro tinha ISBN), entao")
    print("rodar este script de novo duplica o portfolio. Apague imoveis.db para recomecar.")


if __name__ == "__main__":
    main()

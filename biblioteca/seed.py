import os

import httpx

USUARIOS_URL = os.getenv("USUARIOS_URL", "http://localhost:8002")
CATALOGO_URL = os.getenv("CATALOGO_URL", "http://localhost:8001")

USUARIOS = [
    {"nome": "Admin",          "email": "admin@biblioteca.br",   "senha": "admin123", "tipo": "admin"},
    {"nome": "Ana Souza",      "email": "ana@biblioteca.br",     "senha": "senha123", "tipo": "aluno"},
    {"nome": "Carlos Lima",    "email": "carlos@biblioteca.br",  "senha": "senha123", "tipo": "aluno"},
    {"nome": "Joao Melo",      "email": "joao@biblioteca.br",    "senha": "senha123", "tipo": "aluno"},
    {"nome": "Maria Silva",    "email": "maria@biblioteca.br",   "senha": "senha123", "tipo": "aluno"},
    {"nome": "Beatriz Rocha",  "email": "beatriz@biblioteca.br", "senha": "senha123", "tipo": "bibliotecario"},
    {"nome": "Pedro Alves",    "email": "pedro@biblioteca.br",   "senha": "senha123", "tipo": "aluno"},
]

LIVROS = [
    {"titulo": "Clean Code",                      "autor": "Robert C. Martin",    "isbn": "978-0132350884", "ano_publicacao": 2008, "genero": "Tecnologia", "quantidade_total": 3},
    {"titulo": "Design Patterns",                 "autor": "Erich Gamma",         "isbn": "978-0201633610", "ano_publicacao": 1994, "genero": "Tecnologia", "quantidade_total": 2},
    {"titulo": "The Pragmatic Programmer",        "autor": "Andrew Hunt",         "isbn": "978-0135957059", "ano_publicacao": 1999, "genero": "Tecnologia", "quantidade_total": 2},
    {"titulo": "Domain-Driven Design",            "autor": "Eric Evans",          "isbn": "978-0321125217", "ano_publicacao": 2003, "genero": "Tecnologia", "quantidade_total": 1},
    {"titulo": "Refactoring",                     "autor": "Martin Fowler",       "isbn": "978-0134757599", "ano_publicacao": 2018, "genero": "Tecnologia", "quantidade_total": 2},
    {"titulo": "Microservices Patterns",          "autor": "Chris Richardson",    "isbn": "978-1617294549", "ano_publicacao": 2018, "genero": "Tecnologia", "quantidade_total": 2},
    {"titulo": "Clean Architecture",              "autor": "Robert C. Martin",    "isbn": "978-0134494166", "ano_publicacao": 2017, "genero": "Tecnologia", "quantidade_total": 3},
    {"titulo": "Codigo Limpo na Pratica",         "autor": "Sandro Mancuso",      "isbn": "978-8575225837", "ano_publicacao": 2014, "genero": "Tecnologia", "quantidade_total": 1},
    {"titulo": "The Mythical Man-Month",          "autor": "Frederick Brooks",    "isbn": "978-0201835953", "ano_publicacao": 1975, "genero": "Tecnologia", "quantidade_total": 2},
    {"titulo": "Working Effectively Legacy Code", "autor": "Michael Feathers",    "isbn": "978-0131177055", "ano_publicacao": 2004, "genero": "Tecnologia", "quantidade_total": 1},
    {"titulo": "Patterns of Enterprise App",      "autor": "Martin Fowler",       "isbn": "978-0321127426", "ano_publicacao": 2002, "genero": "Tecnologia", "quantidade_total": 2},
    {"titulo": "Head First Design Patterns",      "autor": "Eric Freeman",        "isbn": "978-0596007126", "ano_publicacao": 2004, "genero": "Tecnologia", "quantidade_total": 3},
    {"titulo": "Introduction to Algorithms",      "autor": "Thomas Cormen",       "isbn": "978-0262033848", "ano_publicacao": 2009, "genero": "Tecnologia", "quantidade_total": 2},
    {"titulo": "The Clean Coder",                 "autor": "Robert C. Martin",    "isbn": "978-0137081073", "ano_publicacao": 2011, "genero": "Tecnologia", "quantidade_total": 2},
    {"titulo": "Building Microservices",          "autor": "Sam Newman",          "isbn": "978-1491950357", "ano_publicacao": 2015, "genero": "Tecnologia", "quantidade_total": 2},
    {"titulo": "Test-Driven Development",         "autor": "Kent Beck",           "isbn": "978-0321146533", "ano_publicacao": 2002, "genero": "Tecnologia", "quantidade_total": 1},
    {"titulo": "Pragmatic Thinking and Learning", "autor": "Andy Hunt",           "isbn": "978-1934356050", "ano_publicacao": 2008, "genero": "Tecnologia", "quantidade_total": 1},
    {"titulo": "Soft Skills",                     "autor": "John Sonmez",         "isbn": "978-1617292392", "ano_publicacao": 2014, "genero": "Tecnologia", "quantidade_total": 2},
    {"titulo": "Dom Casmurro",                    "autor": "Machado de Assis",    "isbn": "978-8520925140", "ano_publicacao": 1899, "genero": "Literatura", "quantidade_total": 4},
    {"titulo": "Grande Sertao: Veredas",          "autor": "Guimaraes Rosa",      "isbn": "978-8520938782", "ano_publicacao": 1956, "genero": "Literatura", "quantidade_total": 2},
    {"titulo": "Memorias Postumas de Bras Cubas", "autor": "Machado de Assis",    "isbn": "978-8594318600", "ano_publicacao": 1881, "genero": "Literatura", "quantidade_total": 3},
    {"titulo": "Vidas Secas",                     "autor": "Graciliano Ramos",    "isbn": "978-8501069880", "ano_publicacao": 1938, "genero": "Literatura", "quantidade_total": 3},
    {"titulo": "O Cortico",                       "autor": "Aluisio Azevedo",     "isbn": "978-8508133086", "ano_publicacao": 1890, "genero": "Literatura", "quantidade_total": 2},
    {"titulo": "Capitaes da Areia",               "autor": "Jorge Amado",         "isbn": "978-8535911879", "ano_publicacao": 1937, "genero": "Literatura", "quantidade_total": 3},
    {"titulo": "A Hora da Estrela",               "autor": "Clarice Lispector",   "isbn": "978-8520937235", "ano_publicacao": 1977, "genero": "Literatura", "quantidade_total": 2},
    {"titulo": "Iracema",                         "autor": "Jose de Alencar",     "isbn": "978-8508040834", "ano_publicacao": 1865, "genero": "Literatura", "quantidade_total": 2},
    {"titulo": "Macunaima",                       "autor": "Mario de Andrade",    "isbn": "978-8520933424", "ano_publicacao": 1928, "genero": "Literatura", "quantidade_total": 2},
    {"titulo": "Quincas Borba",                   "autor": "Machado de Assis",    "isbn": "978-8525056962", "ano_publicacao": 1891, "genero": "Literatura", "quantidade_total": 1},
    {"titulo": "1984",                            "autor": "George Orwell",       "isbn": "978-8535914849", "ano_publicacao": 1949, "genero": "Ficcao",     "quantidade_total": 3},
    {"titulo": "A Revolucao dos Bichos",          "autor": "George Orwell",       "isbn": "978-8535909555", "ano_publicacao": 1945, "genero": "Ficcao",     "quantidade_total": 3},
    {"titulo": "Admiravel Mundo Novo",            "autor": "Aldous Huxley",       "isbn": "978-8525056238", "ano_publicacao": 1932, "genero": "Ficcao",     "quantidade_total": 2},
    {"titulo": "Fahrenheit 451",                  "autor": "Ray Bradbury",        "isbn": "978-8576572015", "ano_publicacao": 1953, "genero": "Ficcao",     "quantidade_total": 2},
    {"titulo": "O Conto da Aia",                  "autor": "Margaret Atwood",     "isbn": "978-8532530783", "ano_publicacao": 1985, "genero": "Ficcao",     "quantidade_total": 2},
    {"titulo": "O Senhor dos Aneis",              "autor": "J. R. R. Tolkien",    "isbn": "978-8595084759", "ano_publicacao": 1954, "genero": "Fantasia",   "quantidade_total": 2},
    {"titulo": "O Hobbit",                        "autor": "J. R. R. Tolkien",    "isbn": "978-8595084742", "ano_publicacao": 1937, "genero": "Fantasia",   "quantidade_total": 3},
    {"titulo": "Harry Potter e a Pedra Filosofal","autor": "J. K. Rowling",       "isbn": "978-8532511010", "ano_publicacao": 1997, "genero": "Fantasia",   "quantidade_total": 4},
    {"titulo": "As Cronicas de Narnia",           "autor": "C. S. Lewis",         "isbn": "978-8578278736", "ano_publicacao": 1950, "genero": "Fantasia",   "quantidade_total": 2},
    {"titulo": "A Guerra dos Tronos",             "autor": "George R. R. Martin", "isbn": "978-8556510702", "ano_publicacao": 1996, "genero": "Fantasia",   "quantidade_total": 3},
    {"titulo": "O Nome do Vento",                 "autor": "Patrick Rothfuss",    "isbn": "978-8580442625", "ano_publicacao": 2007, "genero": "Fantasia",   "quantidade_total": 2},
    {"titulo": "Uma Breve Historia do Tempo",     "autor": "Stephen Hawking",     "isbn": "978-8580576672", "ano_publicacao": 1988, "genero": "Ciencia",    "quantidade_total": 2},
    {"titulo": "O Universo numa Casca de Noz",    "autor": "Stephen Hawking",     "isbn": "978-8580576689", "ano_publicacao": 2001, "genero": "Ciencia",    "quantidade_total": 1},
    {"titulo": "Cosmos",                          "autor": "Carl Sagan",          "isbn": "978-8535922906", "ano_publicacao": 1980, "genero": "Ciencia",    "quantidade_total": 2},
    {"titulo": "O Gene Egoista",                  "autor": "Richard Dawkins",     "isbn": "978-8535909562", "ano_publicacao": 1976, "genero": "Ciencia",    "quantidade_total": 2},
    {"titulo": "A Origem das Especies",           "autor": "Charles Darwin",      "isbn": "978-8580330755", "ano_publicacao": 1859, "genero": "Ciencia",    "quantidade_total": 1},
    {"titulo": "Por que o Ceu e Azul",            "autor": "Marcelo Gleiser",     "isbn": "978-8535930412", "ano_publicacao": 2017, "genero": "Ciencia",    "quantidade_total": 2},
    {"titulo": "Sapiens",                         "autor": "Yuval Noah Harari",   "isbn": "978-8525432186", "ano_publicacao": 2011, "genero": "Historia",   "quantidade_total": 3},
    {"titulo": "Homo Deus",                       "autor": "Yuval Noah Harari",   "isbn": "978-8535928198", "ano_publicacao": 2015, "genero": "Historia",   "quantidade_total": 2},
    {"titulo": "21 Licoes para o Seculo 21",      "autor": "Yuval Noah Harari",   "isbn": "978-8535931068", "ano_publicacao": 2018, "genero": "Historia",   "quantidade_total": 2},
    {"titulo": "Armas, Germes e Aco",             "autor": "Jared Diamond",       "isbn": "978-8501058003", "ano_publicacao": 1997, "genero": "Historia",   "quantidade_total": 1},
    {"titulo": "1808",                            "autor": "Laurentino Gomes",    "isbn": "978-8581050478", "ano_publicacao": 2007, "genero": "Historia",   "quantidade_total": 3},
    {"titulo": "Escravidao Volume 1",             "autor": "Laurentino Gomes",    "isbn": "978-8542217391", "ano_publicacao": 2019, "genero": "Historia",   "quantidade_total": 2},
    {"titulo": "O Homem mais Rico da Babilonia",  "autor": "George Clason",       "isbn": "978-8595081512", "ano_publicacao": 1926, "genero": "Negocios",   "quantidade_total": 3},
    {"titulo": "Pai Rico, Pai Pobre",             "autor": "Robert Kiyosaki",     "isbn": "978-8550801483", "ano_publicacao": 1997, "genero": "Negocios",   "quantidade_total": 3},
    {"titulo": "Habitos Atomicos",                "autor": "James Clear",         "isbn": "978-8550807567", "ano_publicacao": 2018, "genero": "Negocios",   "quantidade_total": 4},
    {"titulo": "A Startup Enxuta",                "autor": "Eric Ries",           "isbn": "978-8580581577", "ano_publicacao": 2011, "genero": "Negocios",   "quantidade_total": 2},
    {"titulo": "Rapido e Devagar",                "autor": "Daniel Kahneman",     "isbn": "978-8580573855", "ano_publicacao": 2011, "genero": "Negocios",   "quantidade_total": 2},
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

        print(f"\n== Cadastrando livros ({len(LIVROS)}) ==")
        ok = 0
        for l in LIVROS:
            try:
                r = client.post(f"{CATALOGO_URL}/livros/", json=l)
                if r.status_code == 201:
                    ok += 1
                    print(f"  + {l['titulo']}")
                else:
                    print(f"  . {l['titulo']} ja existe ou invalido (status {r.status_code})")
            except httpx.RequestError:
                print(f"  ! falha ao conectar em {CATALOGO_URL} - o servico de Catalogo esta no ar?")
                return

    print(f"\nConcluido. {ok} livros novos cadastrados. Login admin: admin@biblioteca.br / admin123")


if __name__ == "__main__":
    main()
import sqlite3

def criar_banco():
    conn = sqlite3.connect("auth.db")
    cursor = conn.cursor()

    # Tabela de perfis
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    # Tabela de apps
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            rota TEXT NOT NULL
        )
    """)

    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL,
            email TEXT NOT NULL,
            perfil_id INTEGER,
            FOREIGN KEY (perfil_id) REFERENCES perfis(id)
        )
    """)

    # Tabela de permissões
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            perfil_id INTEGER,
            app_id INTEGER,
            FOREIGN KEY (perfil_id) REFERENCES perfis(id),
            FOREIGN KEY (app_id) REFERENCES apps(id)
        )
    """)

    # Inserções
    perfis = [
        (1, 'admin'),
        (2, 'campo'),
        (3, 'b2b')
    ]

    apps = [
        (1, 'Hub', '/hub'),
        (2, 'OSP Diagnóstico', '/app_OSP_Diagnocts'),
        (3, 'Postes', '/app_postes'),
        (4, 'B2B', '/app_B2B'),
        (5, 'Radar CTO', '/app_radar_cto'),
        (6, 'ETP', '/app_etp')
    ]

    usuarios = [
        (1, 'admin', 'wds2025', 'antonio.cavalcante@fibrasil.com.br', 1),
        (2, 'Ezequiel', 'fiber123', 'teste@teste', 2),
        (3, 'ondacom', 'b2b123', 'teste@teste', 3)
    ]

    permissoes = [
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),  # admin
        (2, 2), (2, 3),                                  # campo
        (3, 4)                                           # b2b
    ]

    cursor.executemany("INSERT OR IGNORE INTO perfis (id, nome) VALUES (?, ?)", perfis)
    cursor.executemany("INSERT OR IGNORE INTO apps (id, nome, rota) VALUES (?, ?, ?)", apps)
    cursor.executemany("INSERT OR IGNORE INTO usuarios (id, nome, senha, email, perfil_id) VALUES (?, ?, ?, ?, ?)", usuarios)
    cursor.executemany("INSERT OR IGNORE INTO permissoes (perfil_id, app_id) VALUES (?, ?)", permissoes)

    conn.commit()
    conn.close()
    print("🎉 Banco criado com sucesso!")

if __name__ == "__main__":
    criar_banco()

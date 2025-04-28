# core/setup_db_postgres.py
from core.db import get_connection

def criar_banco_postgres():
    conn = get_connection()
    cursor = conn.cursor()

    # Criação das tabelas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apps (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            rota TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL,
            email TEXT NOT NULL,
            perfil_id INTEGER REFERENCES perfis(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissoes (
            id SERIAL PRIMARY KEY,
            perfil_id INTEGER REFERENCES perfis(id),
            app_id INTEGER REFERENCES apps(id)
        );
    """)

    # Inserts iniciais
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
        (1,1), (1,2), (1,3), (1,4), (1,5), (1,6),
        (2,2), (2,3),
        (3,4)
    ]

    cursor.executemany("INSERT INTO perfis (id, nome) VALUES (%s, %s) ON CONFLICT DO NOTHING", perfis)
    cursor.executemany("INSERT INTO apps (id, nome, rota) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", apps)
    cursor.executemany("INSERT INTO usuarios (id, nome, senha, email, perfil_id) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING", usuarios)
    cursor.executemany("INSERT INTO permissoes (perfil_id, app_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", permissoes)

    conn.commit()
    conn.close()
    print("🎉 Banco de autenticação no PostgreSQL criado com sucesso!")

if __name__ == "__main__":
    criar_banco_postgres()

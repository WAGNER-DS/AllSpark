#core/auth.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "auth.db"

def check_credentials(username: str, password: str):
    """
    Verifica se o usuário e senha estão corretos.
    Retorna dict com info se sucesso, ou None se falha.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.nome, u.perfil_id, p.nome 
        FROM usuarios u
        JOIN perfis p ON u.perfil_id = p.id
        WHERE u.nome = ? AND u.senha = ?
    """, (username, password))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "perfil_id": row[2],
            "perfil_nome": row[3]
        }
    else:
        return None


def get_apps_por_perfil(perfil_id: int):
    """
    Retorna lista de apps permitidos para o perfil.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.nome, a.rota
        FROM permissoes pm
        JOIN apps a ON pm.app_id = a.id
        WHERE pm.perfil_id = ?
    """, (perfil_id,))

    results = cursor.fetchall()
    conn.close()

    return [{"nome": nome, "rota": rota} for nome, rota in results]

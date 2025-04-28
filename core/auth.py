#core/auth.py

from core.db import get_connection

def check_credentials(username: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.nome, u.perfil_id, p.nome 
        FROM usuarios u
        JOIN perfis p ON u.perfil_id = p.id
        WHERE u.nome = %s AND u.senha = %s
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
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.nome, a.rota
        FROM permissoes pm
        JOIN apps a ON pm.app_id = a.id
        WHERE pm.perfil_id = %s
    """, (perfil_id,))

    results = cursor.fetchall()
    conn.close()

    return [{"nome": nome, "rota": rota} for nome, rota in results]

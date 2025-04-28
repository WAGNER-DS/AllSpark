# core/db.py
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        dbname="seu_banco",
        user="seu_usuario",
        password="sua_senha",
        host="localhost",  # ou IP do servidor
        port="5432"
    )

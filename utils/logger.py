# utils/logger.py
import os
import sqlite3
from datetime import datetime
import pytz

# Caminho para o arquivo do banco de dados SQLite
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs", "otdr_consultas.db"))

def inicializar_db():
    """
    Cria a tabela de logs de consultas OTDR, caso ainda não exista.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas_otdr (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user TEXT,
            ip TEXT,
            uf TEXT,
            municipio TEXT,
            cto TEXT,
            distancia_otdr TEXT,
            lat_cto REAL,
            lon_cto REAL,
            lat_falha REAL,
            lon_falha REAL
        )
    """)
    conn.commit()
    conn.close()

def registrar_consulta(
    user,
    ip,
    uf,
    municipio,
    cto,
    distancia_otdr,
    lat_cto,
    lon_cto,
    lat_falha=None,
    lon_falha=None
):
    """
    Insere uma nova linha na tabela de consultas OTDR.
    """
    # 📅 Corrige o fuso horário para o Brasil
    tz = pytz.timezone("America/Sao_Paulo")
    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO consultas_otdr (
            timestamp, user, ip, uf, municipio, cto, distancia_otdr,
            lat_cto, lon_cto, lat_falha, lon_falha
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        user or "desconhecido",
        ip or "indefinido",
        uf,
        municipio,
        cto,
        distancia_otdr,
        lat_cto,
        lon_cto,
        lat_falha,
        lon_falha
    ))
    conn.commit()
    conn.close()

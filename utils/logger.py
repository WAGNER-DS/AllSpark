#utils/logger.py

import os
import psycopg2
from datetime import datetime
import pytz

# Pega a URL do banco do ambiente
DATABASE_URL = os.getenv("DATABASE_URL")

def inicializar_db():
    """
    Cria a tabela de logs de consultas OTDR, caso ainda não exista.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consultas_otdr (
                id SERIAL PRIMARY KEY,
                "timestamp" TEXT,
                "user" TEXT,
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
    except Exception as e:
        print(f"Erro ao inicializar DB: {e}")

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
    try:
        # Corrige fuso horário para o Brasil
        tz = pytz.timezone("America/Sao_Paulo")
        timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO consultas_otdr (
                "timestamp", "user", ip, uf, municipio, cto, distancia_otdr,
                lat_cto, lon_cto, lat_falha, lon_falha
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            timestamp,
            user or "desconhecido",
            ip or "indefinido",
            uf or "não informado",
            municipio or "não informado",
            cto or "não informado",
            str(distancia_otdr) if distancia_otdr is not None else "0",
            float(lat_cto) if lat_cto is not None else None,
            float(lon_cto) if lon_cto is not None else None,
            float(lat_falha) if lat_falha is not None else None,
            float(lon_falha) if lon_falha is not None else None
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao registrar consulta: {e}")

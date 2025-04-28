# core/db.py

from sqlalchemy import create_engine
import psycopg2
import os

def get_engine():
    db_url = os.getenv("DATABASE_URL")
    return create_engine(db_url)

def get_connection():
    db_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(db_url)

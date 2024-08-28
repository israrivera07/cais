# utils/database.py
import psycopg2
from psycopg2 import sql

def get_engine():
    # Configura la conexión a la base de datos
    conn = psycopg2.connect(
        dbname='mydatabase',
        user='postgres',
        password='isra7303',
        host='localhost',
        port='5432'
    )
    return conn

def create_user_table():
    conn = get_engine()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR PRIMARY KEY,
                email VARCHAR UNIQUE NOT NULL,
                name VARCHAR NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.commit()
    conn.close()

def add_user(username, email, name, password):
    conn = get_engine()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO users (username, email, name, password)
            VALUES (%s, %s, %s, %s)
        """, (username, email, name, password))
        conn.commit()
    conn.close()

def get_user(username):
    conn = get_engine()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM users WHERE username = %s
        """, (username,))
        user = cur.fetchone()
    conn.close()
    return user




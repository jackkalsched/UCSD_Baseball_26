import sqlite3
import os

DB_PATH = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            role TEXT NOT NULL,
            invite_token TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

if not os.path.exists(DB_PATH):
    init_db()

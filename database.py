import sqlite3

def get_connection():
    return sqlite3.connect("school.db", check_same_thread=False)

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        title TEXT,
        description TEXT,
        pdf_path TEXT,
        deadline TEXT,
        status TEXT,
        marks INTEGER,
        feedback TEXT
    )
    """)

    # Default admin
    cur.execute("""
    INSERT OR IGNORE INTO users (username,password,role)
    VALUES ('admin','admin123','Admin')
    """)

    conn.commit()
    conn.close()

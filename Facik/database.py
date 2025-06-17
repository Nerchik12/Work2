import sqlite3

def init_db():
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    
    #таблица сотрудников
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        position TEXT,
        face_encoding BLOB
    )
    """)
    
    #таблица посещений
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        action TEXT CHECK(action IN ('in', 'out')),
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    )
    """)
    
    conn.commit()
    conn.close()

init_db()
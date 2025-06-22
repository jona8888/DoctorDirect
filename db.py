import sqlite3

def init_db():
    conn = sqlite3.connect('search_logs.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            condition TEXT,
            zip_code TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_search(condition, zip_code):
    conn = sqlite3.connect('search_logs.db')
    c = conn.cursor()
    c.execute('INSERT INTO search_logs (condition, zip_code) VALUES (?, ?)', (condition, zip_code))
    conn.commit()
    conn.close()

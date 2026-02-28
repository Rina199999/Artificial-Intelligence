import sqlite3
from datetime import datetime


def log_message(user_input, response):
    conn = sqlite3.connect("bot_history.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user_text TEXT, bot_text TEXT)''')

    cursor.execute("SELECT id FROM logs WHERE user_text = ? AND bot_text = ?", (user_input, response))
    if not cursor.fetchone():
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO logs (timestamp, user_text, bot_text) VALUES (?, ?, ?)",
                       (timestamp, user_input, response))
        conn.commit()
    conn.close()


def save_user_name(name):
    conn = sqlite3.connect("bot_history.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_info (key TEXT PRIMARY KEY, value TEXT)''')
    cursor.execute("INSERT OR REPLACE INTO user_info (key, value) VALUES ('user_name', ?)", (name,))
    conn.commit()
    conn.close()


def load_user_name():
    conn = sqlite3.connect("bot_history.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_info (key TEXT PRIMARY KEY, value TEXT)''')
    cursor.execute("SELECT value FROM user_info WHERE key = 'user_name'")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
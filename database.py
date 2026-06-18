import sqlite3

import sqlite3
import os

# Папка для базы: на Amvera — /data (постоянное хранилище), локально — текущая папка
DB_DIR = os.getenv("DB_DIR", ".")
DB_NAME = os.path.join(DB_DIR, "salon.db")



def init_db():
    """Создаёт базу данных и таблицу для записей (если их ещё нет)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            service TEXT,
            date TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("База данных готова, таблица создана.")


def add_booking(name, phone, service, date, time):
    """Добавляет новую запись клиента в базу."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bookings (name, phone, service, date, time) VALUES (?, ?, ?, ?, ?)",
        (name, phone, service, date, time),
    )
    conn.commit()
    conn.close()


def get_all_bookings():
    """Возвращает все записи из базы (сначала новые)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, phone, service, date, time FROM bookings ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
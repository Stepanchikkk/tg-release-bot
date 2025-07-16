import sqlite3
from bot.models import App
from bot.config import DB_PATH

def init_db():
    """Инициализирует базу данных, если таблица отсутствует."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS apps (
                key TEXT PRIMARY KEY,
                title TEXT,
                link TEXT,
                repo TEXT,
                asset_filters TEXT,
                subscribers_users TEXT,
                subscribers_chats TEXT,
                latest_release TEXT
            )
        ''')
        conn.commit()

def get_all_apps():
    """Возвращает список всех приложений из базы данных."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM apps")
        rows = cursor.fetchall()
        return [App(
            key=row[0],
            title=row[1],
            link=row[2],
            repo=row[3],
            asset_filters=eval(row[4]) if row[4] else [],
            subscribers_users=eval(row[5]) if row[5] else [],
            subscribers_chats=eval(row[6]) if row[6] else [],
            latest_release=row[7]
        ) for row in rows]

def get_app(key: str):
    """Возвращает приложение по ключу."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM apps WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return App(
                key=row[0],
                title=row[1],
                link=row[2],
                repo=row[3],
                asset_filters=eval(row[4]) if row[4] else [],
                subscribers_users=eval(row[5]) if row[5] else [],
                subscribers_chats=eval(row[6]) if row[6] else [],
                latest_release=row[7]
            )
        return None

def save_app(app: App):
    """Сохраняет приложение в базу данных."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO apps (key, title, link, repo, asset_filters, subscribers_users, subscribers_chats, latest_release)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            app.key,
            app.title,
            app.link,
            app.repo,
            str(app.asset_filters),
            str(app.subscribers_users),
            str(app.subscribers_chats),
            app.latest_release
        ))
        conn.commit()

def delete_app(key: str):
    """Удаляет приложение по ключу."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM apps WHERE key = ?", (key,))
        conn.commit()
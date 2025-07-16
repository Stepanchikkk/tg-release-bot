import sqlite3
import json
from bot.models import App
from bot.config import DB_PATH

async def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS apps (
        key TEXT PRIMARY KEY,
        title TEXT,
        link TEXT,
        repo TEXT,
        asset_filters TEXT,
        subscribers_users TEXT,
        subscribers_chats TEXT,
        latest_release TEXT
    )''')
    conn.commit()
    conn.close()

def save_app(app: App):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO apps (
        key, title, link, repo, asset_filters, subscribers_users, subscribers_chats, latest_release
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
        app.key,
        app.title,
        app.link,
        app.repo,
        json.dumps(app.asset_filters),
        json.dumps(app.subscribers_users),
        json.dumps(app.subscribers_chats),
        app.latest_release
    ))
    conn.commit()
    conn.close()

def get_app(key: str) -> App:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM apps WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    if row:
        return App(
            key=row[0],
            title=row[1],
            link=row[2],
            repo=row[3],
            asset_filters=json.loads(row[4]),
            subscribers_users=json.loads(row[5]),
            subscribers_chats=json.loads(row[6]),
            latest_release=row[7]
        )
    return None

def get_all_apps() -> list[App]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM apps')
    rows = c.fetchall()
    conn.close()
    return [App(
        key=row[0],
        title=row[1],
        link=row[2],
        repo=row[3],
        asset_filters=json.loads(row[4]),
        subscribers_users=json.loads(row[5]),
        subscribers_chats=json.loads(row[6]),
        latest_release=row[7]
    ) for row in rows]

def delete_app(key: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM apps WHERE key = ?', (key,))
    conn.commit()
    conn.close()
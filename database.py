import sqlite3
import json
import aiosqlite
import asyncio
from datetime import datetime

DB_NAME = "spam_bot.db"

# Глобальная блокировка для синхронизации операций записи
_write_lock = asyncio.Lock()

async def init_db():
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        await db.execute("PRAGMA journal_mode=WAL")  # включаем WAL
        # Таблица аккаунтов
        await db.execute('''CREATE TABLE IF NOT EXISTS accounts
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER NOT NULL DEFAULT 0,
             platform TEXT NOT NULL,
             credentials TEXT NOT NULL,
             status TEXT DEFAULT 'active',
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        # Проверка наличия колонки user_id (для старых баз)
        cursor = await db.execute("PRAGMA table_info(accounts)")
        columns = [row[1] for row in await cursor.fetchall()]
        if 'user_id' not in columns:
            await db.execute("ALTER TABLE accounts ADD COLUMN user_id INTEGER DEFAULT 0")

        # Таблица шаблонов
        await db.execute('''CREATE TABLE IF NOT EXISTS templates
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER NOT NULL,
             name TEXT NOT NULL,
             platform TEXT NOT NULL,
             text TEXT,
             media_path TEXT,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Таблица кампаний
        await db.execute('''CREATE TABLE IF NOT EXISTS campaigns
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER NOT NULL,
             template_id INTEGER,
             platform TEXT NOT NULL,
             account_id INTEGER,
             contacts TEXT,
             delay_min INTEGER DEFAULT 10,
             delay_max INTEGER DEFAULT 60,
             status TEXT DEFAULT 'pending',
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
             started_at TIMESTAMP,
             completed_at TIMESTAMP)''')

        # Таблица лендингов
        await db.execute('''CREATE TABLE IF NOT EXISTS landings
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT NOT NULL,
             template_name TEXT,
             html_path TEXT,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Таблица подписок
        await db.execute('''CREATE TABLE IF NOT EXISTS subscriptions
            (user_id INTEGER PRIMARY KEY,
             status TEXT DEFAULT 'inactive',
             expires_at TIMESTAMP,
             payment_method TEXT,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Таблица инвойсов
        await db.execute('''CREATE TABLE IF NOT EXISTS invoices
            (invoice_id TEXT PRIMARY KEY,
             user_id INTEGER NOT NULL,
             amount INTEGER NOT NULL,
             method TEXT NOT NULL,
             status TEXT DEFAULT 'pending',
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Таблица пользователей
        await db.execute('''CREATE TABLE IF NOT EXISTS users
            (user_id INTEGER PRIMARY KEY,
             username TEXT,
             first_name TEXT,
             last_name TEXT,
             balance REAL DEFAULT 0,
             is_blocked INTEGER DEFAULT 0,
             registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in await cursor.fetchall()]
        if 'is_blocked' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")
        if 'registered_at' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        if 'balance' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0")

        # Таблица транзакций
        await db.execute('''CREATE TABLE IF NOT EXISTS transactions
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER NOT NULL,
             amount REAL NOT NULL,
             type TEXT,
             description TEXT,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        await db.commit()

# ---------- Аккаунты ----------
async def add_account(user_id: int, platform: str, credentials: dict):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute(
                "INSERT INTO accounts (user_id, platform, credentials) VALUES (?, ?, ?)",
                (user_id, platform, json.dumps(credentials, ensure_ascii=False))
            )
            await db.commit()

async def get_accounts(platform: str = None):
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        if platform:
            cursor = await db.execute("SELECT id, user_id, platform, credentials, status FROM accounts WHERE platform=?", (platform,))
        else:
            cursor = await db.execute("SELECT id, user_id, platform, credentials, status FROM accounts")
        rows = await cursor.fetchall()
        return [{"id": r[0], "user_id": r[1], "platform": r[2], "credentials": json.loads(r[3]), "status": r[4]} for r in rows]

async def get_user_accounts(user_id: int) -> list:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute(
            "SELECT id, platform, credentials, status FROM accounts WHERE user_id=?", (user_id,)
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "platform": r[1], "credentials": json.loads(r[2]), "status": r[3]} for r in rows]

async def get_user_accounts_by_platform(user_id: int, platform: str) -> list:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute(
            "SELECT id, credentials FROM accounts WHERE user_id=? AND platform=?",
            (user_id, platform)
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "credentials": json.loads(r[1])} for r in rows]

async def get_account(account_id: int):
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute("SELECT id, user_id, platform, credentials, status FROM accounts WHERE id=?", (account_id,))
        row = await cursor.fetchone()
        if row:
            return {"id": row[0], "user_id": row[1], "platform": row[2], "credentials": json.loads(row[3]), "status": row[4]}
        return None

# ---------- Шаблоны ----------
async def add_template(user_id: int, name: str, platform: str, text: str, media_path: str = None):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute(
                "INSERT INTO templates (user_id, name, platform, text, media_path) VALUES (?, ?, ?, ?, ?)",
                (user_id, name, platform, text, media_path)
            )
            await db.commit()

async def get_templates(platform: str = None, user_id: int = None):
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        query = "SELECT id, user_id, name, platform, text FROM templates"
        params = []
        conditions = []
        if platform:
            conditions.append("platform=?")
            params.append(platform)
        if user_id:
            conditions.append("user_id=?")
            params.append(user_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [{"id": r[0], "user_id": r[1], "name": r[2], "platform": r[3], "text": r[4]} for r in rows]

async def get_template(template_id: int):
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute("SELECT id, user_id, name, platform, text, media_path FROM templates WHERE id=?", (template_id,))
        row = await cursor.fetchone()
        if row:
            return {"id": row[0], "user_id": row[1], "name": row[2], "platform": row[3], "text": row[4], "media_path": row[5]}
        return None

# ---------- Кампании ----------
async def add_campaign(user_id: int, platform: str, account_id: int, template_id: int, contacts: list, delay_min: int, delay_max: int):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute(
                "INSERT INTO campaigns (user_id, platform, account_id, template_id, contacts, delay_min, delay_max) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, platform, account_id, template_id, json.dumps(contacts), delay_min, delay_max)
            )
            await db.commit()

async def update_campaign_status(campaign_id: int, status: str):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute("UPDATE campaigns SET status=? WHERE id=?", (status, campaign_id))
            await db.commit()

async def get_campaigns(user_id: int = None):
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        if user_id:
            cursor = await db.execute(
                "SELECT id, user_id, platform, status, created_at FROM campaigns WHERE user_id=? ORDER BY created_at DESC",
                (user_id,)
            )
        else:
            cursor = await db.execute(
                "SELECT id, user_id, platform, status, created_at FROM campaigns ORDER BY created_at DESC"
            )
        rows = await cursor.fetchall()
        return [{"id": r[0], "user_id": r[1], "platform": r[2], "status": r[3], "created_at": r[4]} for r in rows]

async def get_campaigns_count(user_id: int = None) -> int:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        if user_id:
            cursor = await db.execute("SELECT COUNT(*) FROM campaigns WHERE user_id=?", (user_id,))
        else:
            cursor = await db.execute("SELECT COUNT(*) FROM campaigns")
        row = await cursor.fetchone()
        return row[0] or 0

# ---------- Лендинги ----------
async def add_landing(name: str, template_name: str, html_path: str):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute(
                "INSERT INTO landings (name, template_name, html_path) VALUES (?, ?, ?)",
                (name, template_name, html_path)
            )
            await db.commit()

async def get_landings_count() -> int:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM landings")
        row = await cursor.fetchone()
        return row[0] or 0

# ---------- Шаблоны (количество) ----------
async def get_templates_count(user_id: int = None) -> int:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        if user_id:
            cursor = await db.execute("SELECT COUNT(*) FROM templates WHERE user_id=?", (user_id,))
        else:
            cursor = await db.execute("SELECT COUNT(*) FROM templates")
        row = await cursor.fetchone()
        return row[0] or 0

# ---------- Подписки ----------
async def get_subscription(user_id: int):
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute("SELECT status, expires_at FROM subscriptions WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return {"status": row[0], "expires_at": row[1]}
        return {"status": "inactive", "expires_at": None}

async def set_subscription(user_id: int, status: str, expires_at: str = None, payment_method: str = None):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute(
                "INSERT OR REPLACE INTO subscriptions (user_id, status, expires_at, payment_method) VALUES (?, ?, ?, ?)",
                (user_id, status, expires_at, payment_method)
            )
            await db.commit()

async def get_active_subscriptions_count() -> int:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE status='active' AND expires_at > ?",
            (datetime.now().isoformat(),)
        )
        row = await cursor.fetchone()
        return row[0] or 0

async def get_expired_subscriptions_count() -> int:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE status='active' AND expires_at <= ?",
            (datetime.now().isoformat(),)
        )
        row = await cursor.fetchone()
        return row[0] or 0

async def get_active_subscriptions_list() -> list:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute(
            "SELECT user_id, expires_at FROM subscriptions WHERE status='active' AND expires_at > ?",
            (datetime.now().isoformat(),)
        )
        rows = await cursor.fetchall()
        return [{"user_id": row[0], "expires_at": row[1]} for row in rows]

# ---------- Инвойсы ----------
async def add_invoice(invoice_id: str, user_id: int, amount: int, method: str):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute(
                "INSERT OR REPLACE INTO invoices (invoice_id, user_id, amount, method) VALUES (?, ?, ?, ?)",
                (invoice_id, user_id, amount, method)
            )
            await db.commit()

async def get_invoice(invoice_id: str):
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute("SELECT * FROM invoices WHERE invoice_id=?", (invoice_id,))
        row = await cursor.fetchone()
        if row:
            return {"invoice_id": row[0], "user_id": row[1], "amount": row[2], "method": row[3], "status": row[4]}
        return None

async def update_invoice_status(invoice_id: str, status: str):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute("UPDATE invoices SET status=? WHERE invoice_id=?", (status, invoice_id))
            await db.commit()

# ---------- Пользователи и баланс ----------
async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in await cursor.fetchall()]
        if not columns:
            return None
        cols_str = ", ".join(columns)
        cursor = await db.execute(f"SELECT {cols_str} FROM users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return dict(zip(columns, row))
        return None

async def add_user(user_id: int, username: str, first_name: str, last_name: str):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            cursor = await db.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in await cursor.fetchall()]
            cols = []
            values = []
            placeholders = []
            if 'user_id' in columns:
                cols.append('user_id'); values.append(user_id); placeholders.append('?')
            if 'username' in columns:
                cols.append('username'); values.append(username); placeholders.append('?')
            if 'first_name' in columns:
                cols.append('first_name'); values.append(first_name); placeholders.append('?')
            if 'last_name' in columns:
                cols.append('last_name'); values.append(last_name); placeholders.append('?')
            if cols:
                query = f"INSERT OR IGNORE INTO users ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
                await db.execute(query, values)
                await db.commit()

async def get_balance(user_id: int) -> float:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return row[0]
        else:
            await add_user(user_id, "", "", "")
            return 0.0

async def update_balance(user_id: int, amount: float):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
            await db.commit()

async def add_transaction(user_id: int, amount: float, type: str, description: str = ""):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute(
                "INSERT INTO transactions (user_id, amount, type, description) VALUES (?, ?, ?, ?)",
                (user_id, amount, type, description)
            )
            await db.commit()
            await update_balance(user_id, amount)

# ---------- Блокировка ----------
async def is_user_blocked(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute("SELECT is_blocked FROM users WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return row[0] == 1
        return False

async def block_user(user_id: int):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (user_id,))
            await db.commit()

async def unblock_user(user_id: int):
    async with _write_lock:
        async with aiosqlite.connect(DB_NAME, timeout=30) as db:
            await db.execute("UPDATE users SET is_blocked=0 WHERE user_id=?", (user_id,))
            await db.commit()

# ---------- Статистика ----------
async def get_users_count() -> int:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] or 0

async def get_inactive_users_count() -> int:
    total = await get_users_count()
    active = await get_active_subscriptions_count()
    return total - active

async def get_replenishments_stats() -> dict:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute(
            "SELECT COUNT(*), SUM(amount) FROM transactions WHERE type='replenish'"
        )
        row = await cursor.fetchone()
        count = row[0] or 0
        total = row[1] or 0.0
        return {"count": count, "total": total}

async def get_subscription_purchases_stats() -> dict:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute(
            "SELECT COUNT(*), SUM(amount) FROM transactions WHERE type='subscription_purchase'"
        )
        row = await cursor.fetchone()
        count = row[0] or 0
        total = row[1] or 0.0
        return {"count": count, "total": total}

# ---------- Для рассылки ----------
async def get_all_users() -> list:
    async with aiosqlite.connect(DB_NAME, timeout=30) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [{"user_id": r[0]} for r in rows]
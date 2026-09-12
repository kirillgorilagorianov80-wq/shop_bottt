import aiosqlite
from datetime import datetime

DB_PATH = "shop.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                price TEXT DEFAULT '',
                photo_id TEXT DEFAULT '',
                category TEXT DEFAULT 'other',
                in_stock INTEGER DEFAULT 1,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS post_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                posted_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_product(name, description, price, photo_id, category, in_stock):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO products (name, description, price, photo_id, category, in_stock) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, description, price, photo_id, category, int(in_stock)),
        )
        await db.commit()
        return cur.lastrowid

async def get_all_products():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT * FROM products ORDER BY id DESC")
        return await cur.fetchall()

async def get_product(pid):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT * FROM products WHERE id=?", (pid,))
        return await cur.fetchone()

async def delete_product(pid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM products WHERE id=?", (pid,))
        await db.commit()

async def toggle_stock(pid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE products SET in_stock = 1 - in_stock WHERE id=?", (pid,))
        await db.commit()

async def log_post(product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO post_log (product_id) VALUES (?)", (product_id,))
        await db.commit()

async def get_last_posted_product():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT product_id FROM post_log ORDER BY id DESC LIMIT 1")
        row = await cur.fetchone()
        return row[0] if row else None

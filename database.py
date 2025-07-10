import sqlite3
from pathlib import Path
import os

DB_PATH = Path(__file__).parent.parent / "data" / "inventory.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables name-based column access
    return conn

def initialize_database():
    if not DB_PATH.exists():
        os.makedirs(DB_PATH.parent, exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()

    # Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        buy_price REAL NOT NULL,
        sell_price REAL NOT NULL,
        price_iqd REAL NOT NULL,
        price_usd REAL NOT NULL,
        expiration_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Sales Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity_sold INTEGER,
        price_at_sale REAL,
        total_price REAL,
        profit REAL,
        sale_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    """)

    # Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        usd_to_iqd_rate REAL DEFAULT 1500,
        low_stock_threshold INTEGER DEFAULT 5
    )
    """)

    # Ensure one row exists in settings
    cursor.execute("INSERT OR IGNORE INTO settings (id) VALUES (1)")

    conn.commit()
    conn.close()

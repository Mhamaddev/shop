import streamlit as st
from db.database import get_connection
from datetime import datetime, timedelta

def get_summary_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantity) FROM products")
    total_quantity = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(profit) FROM sales")
    total_profit = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(quantity_sold) FROM sales")
    total_sold = cursor.fetchone()[0] or 0

    cursor.execute("SELECT low_stock_threshold FROM settings WHERE id = 1")
    low_stock_threshold = cursor.fetchone()[0]

    # Low stock
    cursor.execute("SELECT name, quantity FROM products WHERE quantity <= ?", (low_stock_threshold,))
    low_stock_items = cursor.fetchall()

    # Near expiry (in 7 days)
    cursor.execute("SELECT name, expiration_date FROM products WHERE expiration_date IS NOT NULL")
    today = datetime.today()
    soon = today + timedelta(days=7)
    near_expiry = [row for row in cursor.fetchall() if datetime.strptime(row["expiration_date"], "%Y-%m-%d") <= soon]

    conn.close()
    return {
        "total_products": total_products,
        "total_quantity": total_quantity,
        "total_sold": total_sold,
        "total_p_

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import csv
import io

# --------- Database setup ---------
conn = sqlite3.connect("inventory.db", check_same_thread=False)
c = conn.cursor()

def initialize_db():
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        buy_price_iqd REAL NOT NULL,
        buy_price_usd REAL NOT NULL,
        sell_price_iqd REAL NOT NULL,
        sell_price_usd REAL NOT NULL,
        expiration DATE NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        quantity INTEGER NOT NULL,
        total_price_iqd REAL NOT NULL,
        total_price_usd REAL NOT NULL,
        sell_date DATE NOT NULL,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)
    # Initialize default settings if not exist
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)", ("usd_to_iqd", "1500"))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)", ("low_stock_threshold", "5"))
    conn.commit()

initialize_db()

# --------- Helper functions ---------

def get_setting(key):
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    res = c.fetchone()
    return res[0] if res else None

def set_setting(key, value):
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()

def add_product(name, qty, buy_iqd, buy_usd, sell_iqd, sell_usd, expiration):
    # Check if product exists with same name and expiration -> if yes, update qty and prices (overwrite prices)
    c.execute("""
        SELECT id, quantity FROM products WHERE name = ? AND expiration = ?
    """, (name, expiration))
    res = c.fetchone()
    if res:
        product_id, old_qty = res
        new_qty = old_qty + qty
        c.execute("""
            UPDATE products SET quantity=?, buy_price_iqd=?, buy_price_usd=?, sell_price_iqd=?, sell_price_usd=?
            WHERE id=?
        """, (new_qty, buy_iqd, buy_usd, sell_iqd, sell_usd, product_id))
    else:
        c.execute("""
            INSERT INTO products (name, quantity, buy_price_iqd, buy_price_usd, sell_price_iqd, sell_price_usd, expiration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, qty, buy_iqd, buy_usd, sell_iqd, sell_usd, expiration))
    conn.commit()

def get_stock(search=None):
    if search:
        c.execute("SELECT * FROM products WHERE name LIKE ? ORDER BY expiration", (f"%{search}%",))
    else:
        c.execute("SELECT * FROM products ORDER BY expiration")
    return c.fetchall()

def sell_product(product_id, qty):
    c.execute("SELECT quantity, sell_price_iqd, sell_price_usd FROM products WHERE id = ?", (product_id,))
    res = c.fetchone()
    if not res:
        return False, "Product not found"
    available_qty, sell_iqd, sell_usd = res
    if qty > available_qty:
        return False, f"Only {available_qty} items available"
    new_qty = available_qty - qty
    c.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_qty, product_id))
    total_iqd = sell_iqd * qty
    total_usd = sell_usd * qty
    c.execute("""
        INSERT INTO sales (product_id, quantity, total_price_iqd, total_price_usd, sell_date)
        VALUES (?, ?, ?, ?, ?)
    """, (product_id, qty, total_iqd, total_usd, datetime.now().date()))
    conn.commit()
    return True, "Sold successfully"

def get_sales_history():
    c.execute("""
        SELECT s.id, p.name, s.quantity, s.total_price_iqd, s.total_price_usd, s.sell_date
        FROM sales s JOIN products p ON s.product_id = p.id ORDER BY s.sell_date DESC
    """)
    return c.fetchall()

def calculate_profit():
    # Profit = (sell price - buy price) * sold qty
    c.execute("""
    SELECT p.name, s.quantity, p.buy_price_iqd, s.total_price_iqd
    FROM sales s
    JOIN products p ON s.product_id = p.id
    """)
    rows = c.fetchall()
    profit = 0.0
    for name, sold_qty, buy_iqd, total_sell_iqd in rows:
        cost = buy_iqd * sold_qty
        profit += (total_sell_iqd - cost)
    return profit

# --------- Streamlit UI ---------

st.set_page_config(page_title="Inventory System", layout="wide")

st.sidebar.title("Inventory System")
menu = st.sidebar.radio("Go to", ["Dashboard", "Buy", "Sell", "Stock", "Sales History", "Settings"])

usd_to_iqd = float(get_setting("usd_to_iqd"))
low_stock_threshold = int(get_setting("low_stock_threshold"))

if menu == "Dashboard":
    st.title("Dashboard")

    c.execute("SELECT COUNT(*) FROM products")
    total_products = c.fetchone()[0]

    c.execute("SELECT SUM(quantity) FROM products")
    total_qty = c.fetchone()[0] or 0

    profit = calculate_profit()

    st.metric("Total Product Types", total_products)
    st.metric("Total Quantity in Stock", total_qty)
    st.metric("Total Profit (IQD)", f"{profit:,.2f}")

    st.markdown("### Low Stock Alerts")
    c.execute("SELECT name, quantity FROM products WHERE quantity <= ? ORDER BY quantity ASC", (low_stock_threshold,))
    low_stock = c.fetchall()
    if low_stock:
        for name, qty in low_stock:
            st.warning(f"Low stock: {name} ({qty})")
    else:
        st.success("No low stock items")

    st.markdown("### Expiring Soon (within 7 days)")
    today = datetime.now().date()
    near_exp = today + timedelta(days=7)
    c.execute("SELECT name, expiration FROM products WHERE expiration <= ? ORDER BY expiration ASC", (near_exp,))
    expiring = c.fetchall()
    if expiring:
        for name, exp_date in expiring:
            st.warning(f"Expiring soon: {name} (Expires on {exp_date})")
    else:
        st.success("No items expiring soon")

elif menu == "Buy":
    st.title("Buy Products")
    with st.form("buy_form", clear_on_submit=True):
        name = st.text_input("Product Name", max_chars=50)
        qty = st.number_input("Quantity", min_value=1, step=1)
        buy_price_iqd = st.number_input("Buying Price (IQD)", min_value=0.0, format="%.2f")
        buy_price_usd = st.number_input("Buying Price (USD)", min_value=0.0, format="%.2f")
        sell_price_iqd = st.number_input("Selling Price (IQD)", min_value=0.0, format="%.2f")
        sell_price_usd = st.number_input("Selling Price (USD)", min_value=0.0, format="%.2f")
        expiration = st.date_input("Expiration Date")
        submitted = st.form_submit_button("Add to Stock")
        if submitted:
            if not name.strip():
                st.error("Product name is required.")
            elif sell_price_iqd < buy_price_iqd or sell_price_usd < buy_price_usd:
                st.error("Selling price should be >= buying price.")
            else:
                add_product(name.strip(), qty, buy_price_iqd, buy_price_usd, sell_price_iqd, sell_price_usd, expiration)
                st.success(f"Added {qty} units of {name} to stock.")

elif menu == "Sell":
    st.title("Sell Products")
    stock = get_stock()
    if not stock:
        st.info("No products in stock.")
    else:
        stock_dict = {f"{p[1]} (Exp: {p[7]}) - Qty: {p[2]}": p for p in stock if p[2] > 0}
        product_key = st.selectbox("Select product to sell", options=list(stock_dict.keys()))
        selected_product = stock_dict.get(product_key)
        if selected_product:
            max_qty = selected_product[2]
            qty = st.number_input("Quantity to sell", min_value=1, max_value=max_qty, step=1)
            if st.button("Sell"):
                success, msg = sell_product(selected_product[0], qty)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

elif menu == "Stock":
    st.title("Stock List")
    search = st.text_input("Search product by name")
    products = get_stock(search)
    if products:
        df = pd.DataFrame(products, columns=["ID", "Name", "Quantity", "Buy Price IQD", "Buy Price USD", "Sell Price IQD", "Sell Price USD", "Expiration"])
        st.dataframe(df.style.format({"Buy Price IQD": "{:,.2f}", "Buy Price USD": "{:,.2f}", "Sell Price IQD": "{:,.2f}", "Sell Price USD": "{:,.2f}"}))
    else:
        st.info("No products found.")

elif menu == "Sales History":
    st.title("Sales History")
    sales = get_sales_history()
    if sales:
        df = pd.DataFrame(sales, columns=["Sale ID", "Product Name", "Quantity", "Total Price IQD", "Total Price USD", "Date"])
        st.dataframe(df.style.format({"Total Price IQD": "{:,.2f}", "Total Price USD": "{:,.2f}"}))

        # Export CSV
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button("Download CSV", data=csv_buffer.getvalue(), file_name="sales_history.csv", mime="text/csv")
    else:
        st.info("No sales history.")

elif menu == "Settings":
    st.title("Settings")

    usd_rate = st.number_input("USD to IQD Exchange Rate", value=usd_to_iqd, min_value=0.1, format="%.2f")
    low_stock = st.number_input("Low Stock Threshold", value=low_stock_threshold, min_value=1, step=1)
    if st.button("Save Settings"):
        set_setting("usd_to_iqd", str(usd_rate))
        set_setting("low_stock_threshold", str(low_stock))
        st.success("Settings saved.")


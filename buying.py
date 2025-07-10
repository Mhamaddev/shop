import streamlit as st
import sqlite3
from db.database import get_connection

def insert_product(name, quantity, buy_price, sell_price, price_iqd, price_usd, expiration_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, quantity, buy_price, sell_price, price_iqd, price_usd, expiration_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, quantity, buy_price, sell_price, price_iqd, price_usd, expiration_date))
    conn.commit()
    conn.close()

def show():
    st.title("🛒 Buy Items")

    st.subheader("Add a New Product to Inventory")

    with st.form("buy_form"):
        name = st.text_input("Item Name")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        buy_price = st.number_input("Buy Price (per item)", min_value=0.0, step=0.01)
        sell_price = st.number_input("Sell Price (per item)", min_value=0.0, step=0.01)
        price_iqd = st.number_input("Price in IQD", min_value=0.0, step=0.01)
        price_usd = st.number_input("Price in USD", min_value=0.0, step=0.01)
        expiration_date = st.date_input("Expiration Date")

        submitted = st.form_submit_button("Add to Inventory")
        if submitted:
            insert_product(name, quantity, buy_price, sell_price, price_iqd, price_usd, expiration_date.strftime('%Y-%m-%d'))
            st.success(f"{quantity} units of '{name}' added to inventory.")

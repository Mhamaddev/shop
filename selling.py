import streamlit as st
import sqlite3
from db.database import get_connection
from datetime import datetime

def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE quantity > 0 ORDER BY name")
    products = cursor.fetchall()
    conn.close()
    return products

def record_sale(product_id, quantity_sold, price_at_sale, total_price, profit):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO sales (product_id, quantity_sold, price_at_sale, total_price, profit) VALUES (?, ?, ?, ?, ?)",
                   (product_id, quantity_sold, price_at_sale, total_price, profit))

    cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity_sold, product_id))

    conn.commit()
    conn.close()

def show():
    st.title("💰 Sell Items")

    products = get_all_products()
    if not products:
        st.warning("No stock available for sale.")
        return

    product_names = [f"{p['name']} (Qty: {p['quantity']})" for p in products]
    selected_index = st.selectbox("Select Product", range(len(product_names)), format_func=lambda i: product_names[i])

    selected_product = products[selected_index]

    st.write(f"**Selling Price:** {selected_product['sell_price']} per unit")

    quantity = st.number_input("Quantity to Sell", min_value=1, max_value=selected_product['quantity'], step=1)

    if st.button("Sell"):
        total = quantity * selected_product['sell_price']
        cost = quantity * selected_product['buy_price']
        profit = total - cost
        record_sale(
            product_id=selected_product['id'],
            quantity_sold=quantity,
            price_at_sale=selected_product['sell_price'],
            total_price=total,
            profit=profit
        )
        st.success(f"Sold {quantity} units of {selected_product['name']} for total {total} (Profit: {profit})")

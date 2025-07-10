import streamlit as st
from db.database import get_connection

def show():
    st.title("🧾 Sales History")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sales.*, products.name 
        FROM sales
        LEFT JOIN products ON sales.product_id = products.id
        ORDER BY sale_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    if rows:
        st.dataframe([{**dict(row), "product_name": row["name"]} for row in rows])
    else:
        st.info("No sales recorded yet.")

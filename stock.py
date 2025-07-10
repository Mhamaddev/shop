import streamlit as st
from db.database import get_connection

def show():
    st.title("📦 Current Stock")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY expiration_date ASC")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        st.dataframe([{key: row[key] for key in row.keys()} for row in rows])
    else:
        st.info("No items in stock.")

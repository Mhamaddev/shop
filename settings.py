import streamlit as st
from db.database import get_connection

def get_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings WHERE id = 1")
    settings = cursor.fetchone()
    conn.close()
    return settings

def update_settings(usd_to_iqd, low_stock):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET usd_to_iqd_rate = ?, low_stock_threshold = ? WHERE id = 1",
                   (usd_to_iqd, low_stock))
    conn.commit()
    conn.close()

def show():
    st.title("⚙️ Settings")

    current = get_settings()

    usd_to_iqd = st.number_input("USD to IQD Rate", value=current['usd_to_iqd_rate'], step=10.0)
    low_stock = st.number_input("Low Stock Threshold", value=current['low_stock_threshold'], step=1)

    if st.button("Update Settings"):
        update_settings(usd_to_iqd, low_stock)
        st.success("Settings updated.")

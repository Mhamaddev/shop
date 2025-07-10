import streamlit as st
from db.database import initialize_database
from pages import dashboard, buying, selling, stock, settings, sales_history

# Initialize the database (create tables if they don't exist)
initialize_database()

# Sidebar navigation
st.sidebar.title("🧾 Inventory System")
page = st.sidebar.radio("Go to", ["Dashboard", "Buy Items", "Sell Items", "Stock", "Sales History", "Settings"])

# Routing
if page == "Dashboard":
    dashboard.show()
elif page == "Buy Items":
    buying.show()
elif page == "Sell Items":
    selling.show()
elif page == "Stock":
    stock.show()
elif page == "Sales History":
    sales_history.show()
elif page == "Settings":
    settings.show()

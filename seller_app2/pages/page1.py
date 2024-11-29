from navigation import make_sidebar
import streamlit as st
from datetime import datetime, timedelta
import fb_utils2 as fb
import pandas as pd

@st.dialog("Date Error")
def date_error():
    st.write(f"The 'From' date must be before the 'To' date.")

hide_navigation_style = """
    <style>
    [data-testid="stSidebarNav"] > ul:first-child {
        display: none;
    }
    </style>
"""
st.markdown(hide_navigation_style, unsafe_allow_html=True)

make_sidebar()

st.title("📈Sales Analytics")

if 'idToken' in st.session_state and 'email' in st.session_state:
    idToken = st.session_state['idToken']
    user = st.session_state['email']
            
    st.header("Total Sales per Day🚀💸", divider="green")
    col1, col2 = st.columns(2)

    with col1:
        from_date_sales = st.date_input("From:", datetime.today() - timedelta(days=7), key="from_date_sales")  # Use datetime.date object

    with col2:
        to_date_sales = st.date_input("To:", datetime.today(), key="to_date_sales")

    if from_date_sales > to_date_sales:
        date_error()
    else:
        date, total = fb.get_sales(idToken, user, from_date_sales, to_date_sales)
        sales_data = pd.DataFrame({"Sales": total}, index=date)
        st.area_chart(sales_data)

    st.header("Menu Rankings🥤🥗🍔🍗🍟🥓", divider="red")
    col1, col2 = st.columns(2)

    with col1:
        from_date_menu = st.date_input("From:", datetime.today() - timedelta(days=7), key="from_date_menu")  # Use datetime.date object

    with col2:
        to_date_menu = st.date_input("To:", datetime.today(), key="to_date_menu")

    if from_date_menu > to_date_menu:
        if from_date_sales > to_date_sales:
            pass
        else:
            date_error()
    else:
        menu, counts = fb.get_menuranks(idToken, user, from_date_menu, to_date_menu)
        menuranks_data = pd.DataFrame({"Counts":counts}, index=menu)
        st.bar_chart(menuranks_data)

else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()
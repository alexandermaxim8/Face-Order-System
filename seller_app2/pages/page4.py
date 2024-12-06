import streamlit as st
from navigation import make_sidebar
from fb_utils2 import get_menu, log_menu
from datetime import datetime, timezone, timedelta
# from fb_utils2 import get_favorites # jika ingin implementasi favorites terpisah
# from navigation import make_sidebar  # jika dibutuhkan
import requests

def check_login():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("Anda belum login. Mengarahkan ke halaman login...")
        st.session_state.logged_in = False
        st.session_state.clear()
        st.switch_page("login.py")

# Panggil fungsi ini di awal halaman
check_login()

hide_navigation_style = """
    <style>
    [data-testid="stSidebarNav"] > ul:first-child {
        display: none;
    }
    </style>
"""
st.markdown(hide_navigation_style, unsafe_allow_html=True)
make_sidebar()

st.title("🍽️ Order Menu")
st.write("Welcome, how do you want to make the order?")


order_type = st.radio("Pilih Metode Pemesanan:", ["Manually", "Registered Favorite"])

idToken = st.session_state.get('idToken')
user = st.session_state.get('email')

if idToken and user:
    menu_list = get_menu(idToken, user)
    menus = {doc['fields']['name']['stringValue']: int(doc['fields']['price']['integerValue']) for doc in menu_list}

    selected_items = {}
    st.subheader("Pilih Menu")

    if order_type == "Manually":
        st.info("Silakan pilih menu secara manual dari daftar berikut:")
        for m_name, m_price in menus.items():
            qty = st.number_input(f"{m_name} - Rp.{m_price}", min_value=0, step=1, key=m_name)
            if qty > 0:
                selected_items[m_name] = (m_price, qty)
    else:
        st.info("Pilih dari menu favorit (sementara gunakan data yang sama):")
        for m_name, m_price in menus.items():
            qty = st.number_input(f"{m_name} - Rp.{m_price}", min_value=0, step=1, key="fav_" + m_name)
            if qty > 0:
                selected_items[m_name] = (m_price, qty)
    
    if st.button("Place Order"):
        if len(selected_items) == 0:
            st.error("Anda belum memilih menu apapun!")
        else:
            total = 0
            st.subheader("Ringkasan Pesanan Anda")
            # Buat array menu dalam format Firestore
            menu_array = []
            for item, (price, qty) in selected_items.items():
                subtotal = price * qty
                st.write(f"{item} x {qty} - Rp.{subtotal}")
                total += subtotal
                # Masukkan item ke dalam bentuk Firestore arrayValue
                menu_array.append({
                    "mapValue": {
                        "fields": {
                            "name": {"stringValue": item},
                            "price": {"integerValue": str(price)},
                            "quantity": {"integerValue": str(qty)}
                        }
                    }
                })
            
            st.write(f"**Total: Rp.{total}**")
            st.success("Your food is being cooked, wait and enjoy!")
            st.balloons()

            # Log menu ke Firestore
            # Gunakan timestamp atau ID unik untuk 'id'
            # Panggil fungsi log_menu
            result = log_menu(idToken, user, menu_array,0)
            if result:
                # Anda dapat memeriksa respons jika log_menu mengembalikan response JSON
                # Misal: st.write("Menu logged successfully!")
                pass
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()
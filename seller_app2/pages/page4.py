import streamlit as st
from navigation import make_sidebar
from fb_utils2 import get_menu, log_menu
from datetime import datetime, timezone, timedelta

def check_login():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("Anda belum login. Mengarahkan ke halaman login...")
        st.session_state.logged_in = False
        st.session_state.clear()
        st.switch_page("login.py")

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
    # Ambil data menu hanya saat pertama kali halaman dibuka atau saat tidak ada di session_state
    if "menus" not in st.session_state:
        menu_list = get_menu(idToken, user)
        st.session_state.menus = {
            doc['fields']['name']['stringValue']: int(doc['fields']['price']['integerValue']) 
            for doc in menu_list
        }

    menus = st.session_state.menus

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
            menu_array = []
            for item, (price, qty) in selected_items.items():
                subtotal = price * qty
                st.write(f"{item} x {qty} - Rp.{subtotal}")
                total += subtotal
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

            # Barulah di sini kita tulis ke Firebase
            order_id = int(datetime.now().timestamp())
            result = log_menu(idToken, user, menu_array, order_id)
            if result:
                st.write("Menu logged successfully!")
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()

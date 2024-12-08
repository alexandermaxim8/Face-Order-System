import streamlit as st
from navigation import make_sidebar
from fb_utils2 import get_menu, log_menu
from datetime import datetime, timezone, timedelta

if 'first_visit_manual' not in st.session_state:
    st.session_state.first_visit_manual = True
    st.cache_resource.clear()

if st.session_state.first_visit_manual:
    keys_to_keep = ["guest_in", "logged_in", "email", "first_visit_manual"]
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]
    st.session_state.first_visit_manual = False


def check_login():
    if 'guest_in' not in st.session_state or not st.session_state['guest_in']:
        st.warning("Anda belum login. Mengarahkan ke halaman login...")
        st.session_state.guest_in = False
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

user = st.session_state.get('email')

if user:
    # Ambil data menu hanya saat pertama kali halaman dibuka atau saat tidak ada di session_state
    if "menus" not in st.session_state:
        menu_list = get_menu(user)
        st.session_state.menus = {
            doc['fields']['name']['stringValue']: int(doc['fields']['price']['integerValue']) 
            for doc in menu_list
        }

    menus = st.session_state.menus

    selected_items = {}
    st.subheader("Choose Menu")

    st.info("Silakan pilih menu secara manual dari daftar berikut:")
    for m_name, m_price in menus.items():
        qty = st.number_input(f"{m_name} - Rp.{m_price}", min_value=0, step=1, key=m_name)
        if qty > 0:
            selected_items[m_name] = (m_price, qty)
    
    if st.button("Place Order", type="primary"):
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
            # order_id = int(datetime.now().timestamp())
            result = log_menu(user, menu_array, 0)
            if result:
                st.write("Menu logged successfully!")
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()
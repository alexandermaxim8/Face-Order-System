
# # Sembunyikan navigasi sidebar
# hide_navigation_style = """
#     <style>
#     [data-testid="stSidebarNav"] > ul:first-child {
#         display: none;
#     }
#     </style>
# """
# st.markdown(hide_navigation_style, unsafe_allow_html=True)

# from navigation import make_sidebar
# import streamlit as st
# # Form untuk menambahkan menu
# st.header("Tambah Menu Makanan Baru")
# menu_name = st.text_input("Nama Menu:")
# menu_price = st.number_input("Harga Menu:", min_value=0)

# if st.button("Tambah Menu"):
#     if menu_name and menu_price:
#         #add_menu(menu_name, menu_price, idToken, user)
#         st.success(f"Menu '{menu_name}' berhasil ditambahkan!")
#     else:
#         st.error("Silakan isi nama dan harga menu.")

   
from navigation import make_sidebar
import streamlit as st
from fb_utils2 import add_menu

# Sembunyikan navigasi sidebar (opsional)
hide_navigation_style = """
    <style>
    [data-testid="stSidebarNav"] > ul:first-child {
        display: none;
    }
    </style>
"""
st.markdown(hide_navigation_style, unsafe_allow_html=True)

make_sidebar()

# Cek apakah pengguna sudah login
if 'idToken' in st.session_state and 'email' in st.session_state:
    idToken = st.session_state['idToken']
    user = st.session_state['email']
    
    # Form untuk menambahkan menu
    st.header("Tambah Menu Makanan Baru")
    menu_name = st.text_input("Nama Menu:")
    menu_price = st.number_input("Harga Menu:", min_value=0)
    
    if st.button("Tambah Menu"):
        if menu_name and menu_price:
            # Panggil fungsi add_menu untuk menambahkan menu ke Firebase
            result = add_menu(menu_name, menu_price, idToken, user)
            if result.get('success'):
                st.success(f"Menu '{menu_name}' berhasil ditambahkan!")
            else:
                st.error(f"Gagal menambahkan menu: {result.get('error')}")
        else:
            st.error("Silakan isi nama dan harga menu.")
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()

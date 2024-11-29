from navigation import make_sidebar
import streamlit as st
from fb_utils2 import add_menu, update_menu, get_menu

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

    # Form untuk mengedit menu
    st.header("Edit Menu Makanan")
    menu_list = get_menu(idToken, user)  # Ambil semua menu dari Firebase
    menu_options = {doc['fields']['name']['stringValue']: doc['name'].split('/')[-1] for doc in menu_list}
    
    selected_menu = st.selectbox("Pilih Menu untuk Diedit:", options=menu_options.keys())
    new_name = st.text_input("Nama Baru:", selected_menu)
    new_price = st.number_input("Harga Baru:", min_value=0, value=0)
    
    if st.button("Edit Menu"):
        if selected_menu and (new_name or new_price):
            menu_id = menu_options[selected_menu]
            result = update_menu(idToken, user, menu_id, new_name, new_price)
            if result.get('success'):
                st.success(f"Menu '{selected_menu}' berhasil diperbarui menjadi '{new_name}' dengan harga {new_price}.")
            else:
                st.error(f"Gagal memperbarui menu: {result.get('error')}")
        else:
            st.error("Silakan isi nama baru atau harga baru untuk menu yang dipilih.")
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()

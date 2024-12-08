from navigation import make_sidebar
import streamlit as st
from fb_utils2 import add_menu, update_menu, get_menu, delete_menu

def check_login():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("Anda belum login. Mengarahkan ke halaman login...")
        st.session_state.logged_in = False
        st.session_state.clear()
        st.switch_page("login.py")

check_login()

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

st.title("🍔Menubase")
st.header("New Menu➕", divider="orange")

if 'idToken' in st.session_state and 'email' in st.session_state:
    idToken = st.session_state['idToken']
    user = st.session_state['email']
        
    # Form untuk menambahkan menu
    menu_name = st.text_input("Nama Menu:")
    menu_price = st.number_input("Harga Menu:", min_value=0)

    if st.button("Add"):
        if menu_name and menu_price:
            result = add_menu(menu_name, menu_price, user)
            if result.get('success'):
                st.success(f"Menu '{menu_name}' berhasil ditambahkan!")
            else:
                st.error(f"Gagal menambahkan menu: {result.get('error')}")
        else:
            st.error("Silakan isi nama dan harga menu.")

    # Form untuk mengedit menu
    st.header("Edit Menu⭕", divider="violet")
    menu_list = get_menu(user)  # Ambil semua menu dari Firebase
    menu_options = {doc['fields']['name']['stringValue']: doc['name'].split('/')[-1] for doc in menu_list}

    selected_menu = st.selectbox("Pilih Menu untuk Diedit:", options=menu_options.keys())
    new_name = st.text_input("Nama Baru:", selected_menu)
    new_price = st.number_input("Harga Baru:", min_value=0, value=0)

    if st.button("Edit"):
        if selected_menu and (new_name or new_price):
            menu_id = menu_options[selected_menu]
            result = update_menu(user, menu_id, new_name, new_price)
            if result.get('success'):
                st.success(f"Menu '{selected_menu}' berhasil diperbarui menjadi '{new_name}' dengan harga {new_price}.")
            else:
                st.error(f"Gagal memperbarui menu: {result.get('error')}")
        else:
            st.error("Silakan isi nama baru atau harga baru untuk menu yang dipilih.")

    # Form untuk menghapus menu
    st.header("Hapus Menu🗑️", divider="red")
    selected_menu_delete = st.selectbox("Pilih Menu untuk Dihapus:", options=menu_options.keys(), key="delete_select")
    if st.button("Delete"):
        if selected_menu_delete:
            menu_id_delete = menu_options[selected_menu_delete]
            result = delete_menu(user, menu_id_delete)
            if result.get('success'):
                st.success(f"Menu '{selected_menu_delete}' berhasil dihapus!")
                # Setelah menghapus, kita refresh daftar menu
                menu_list = get_menu(user) 
                menu_options = {doc['fields']['name']['stringValue']: doc['name'].split('/')[-1] for doc in menu_list}
            else:
                st.error(f"Gagal menghapus menu: {result.get('error')}")
        else:
            st.error("Silakan pilih menu yang ingin dihapus.")

else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()
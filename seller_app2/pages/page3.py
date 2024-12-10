import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from navigation import make_sidebar
import fb_utils2 as fb

# saat refresh website, maka akan kembali ke halaman login
def check_login():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("Anda belum login. Mengarahkan ke halaman login...")
        st.session_state.logged_in = False
        st.session_state.clear()
        st.switch_page("login.py")

# Panggil fungsi ini di awal setiap halaman
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

# Memanggil fungsi untuk membuat sidebar
make_sidebar()

st.title("🛒 Riwayat Pesanan Terakhir")

# Refresh button
if st.button("🔄 Refresh"):
    # Menandai bahwa data perlu diperbarui
    st.session_state.refresh_data = True

# Memeriksa apakah pengguna telah login
if 'idToken' in st.session_state and 'email' in st.session_state:
    idToken = st.session_state['idToken']
    user = st.session_state['email']
    
    # Mengambil data hanya jika diperlukan (atau jika tombol refresh ditekan)
    if "refresh_data" not in st.session_state or st.session_state.refresh_data:
        if "selected_orders" in st.session_state:
            selected_orders = st.session_state.selected_orders
        else:
            selected_orders = pd.DataFrame(columns=["No", "Pilih", "Waktu Pesanan", "Item Pesanan", "Total Harga"])
        
        # Pass selected orders to the function if they exist
        if not selected_orders.empty:
            selected_order_times = selected_orders["Waktu Pesanan"].tolist()
            json_response = fb.get_recent_order(user, selected_order_times, limit=10)
        else:
            json_response = fb.get_recent_order(user, limit=10)
        
        st.session_state.refresh_data = False  # Reset flag setelah data diambil
        st.session_state.json_response = json_response
    else:
        json_response = st.session_state.json_response

    # Display orders if available
    if "document" in json_response[0]:
        orders = []
        for idx, doc in enumerate(json_response, start=1):
            fields = doc["document"]["fields"]
            if not fields.get("menu") or not fields["menu"].get("arrayValue") or not fields["menu"]["arrayValue"].get("values"):
                continue
            id = fields["id"]["integerValue"]
            order_time = datetime.fromisoformat(fields["datetime"]["timestampValue"].replace("Z", "+00:00"))
            order_time = order_time.astimezone(timezone(timedelta(hours=7)))

            menu_items = fields["menu"]["arrayValue"]["values"]
            
            # Mengumpulkan item pesanan dengan quantity
            item_list = []
            total_price = 0
            for item in menu_items:
                item_fields = item["mapValue"]["fields"]
                name = item_fields["name"]["stringValue"]
                price = int(item_fields["price"]["integerValue"])
                quantity = int(item_fields["quantity"]["integerValue"]) if "quantity" in item_fields else 1

                # Tambahkan ke daftar item
                item_list.append(f"{quantity}-{name}")
                # Hitung total harga
                total_price += price * quantity

            orders.append({
                "No": id,  # Kolom nomor urut
                "Pilih": False,  # Kolom checkbox
                "Waktu Pesanan": order_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Item Pesanan": ", ".join(item_list),
                "Total Harga": f"Rp{total_price:,}"
            })

        # Membuat DataFrame dari data pesanan
        df_orders = pd.DataFrame(orders)

        # Menampilkan tabel menggunakan st.data_editor dengan konfigurasi kolom checkbox
        edited_df = st.data_editor(
            df_orders,
            column_config={
                "Pilih": st.column_config.CheckboxColumn(
                    label="Pilih",
                    help="Centang untuk memilih pesanan ini",
                    default=False
                )
            },
            hide_index=True,  # Menyembunyikan indeks default
            use_container_width=True,
            height=200  # Sesuaikan tinggi tabel sesuai kebutuhan
        )

        # Menyimpan selected orders ke session_state untuk digunakan saat refresh berikutnya
        selected_orders = edited_df[edited_df["Pilih"]]
        st.session_state.selected_orders = selected_orders

        # Menampilkan data pesanan yang dipilih
        if not selected_orders.empty:
            st.subheader("Pesanan yang Sudah Selesai")
            # Pada tampilan ini, item pesanan sudah termasuk quantity
            st.table(selected_orders.drop(columns=["Pilih"]))
        else:
            st.info("Tidak ada pesanan yang dipilih.")
    else:
        st.info("Tidak ada data pesanan yang ditemukan.")
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()
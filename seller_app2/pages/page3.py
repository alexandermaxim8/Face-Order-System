import streamlit as st
import pandas as pd
from datetime import datetime
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


if st.button("🔄 Refresh"):
    # Menandai bahwa data perlu diperbarui
    st.session_state.refresh_data = True

# Memeriksa apakah pengguna telah login
if 'idToken' in st.session_state and 'email' in st.session_state:
    idToken = st.session_state['idToken']
    user = st.session_state['email']
    
    # Mengambil data hanya jika diperlukan (atau jika tombol refresh ditekan)
    if "refresh_data" not in st.session_state or st.session_state.refresh_data:
        json_response = fb.get_recent_order(idToken, user, limit=10)
        st.session_state.refresh_data = False  # Reset flag setelah data diambil
        st.session_state.json_response = json_response
    else:
        json_response = st.session_state.json_response


    if "document" in json_response[0]:
        orders = []
        for idx, doc in enumerate(json_response, start=1):
            fields = doc["document"]["fields"]
            order_time = datetime.fromisoformat(fields["datetime"]["timestampValue"].replace("Z", "+00:00"))
            order_items = [item["mapValue"]["fields"]["name"]["stringValue"] for item in fields["menu"]["arrayValue"]["values"]]
            total_price = sum(int(item["mapValue"]["fields"]["price"]["integerValue"]) for item in fields["menu"]["arrayValue"]["values"])
            orders.append({
                "No": idx,  # Kolom nomor urut
                "Pilih": False,  # Kolom checkbox
                "Waktu Pesanan": order_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Item Pesanan": ", ".join(order_items),
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

        # Menampilkan data pesanan yang dipilih
        selected_orders = edited_df[edited_df["Pilih"]]
        if not selected_orders.empty:
            st.subheader("Pesanan yang Sudah Selesai")
            st.table(selected_orders.drop(columns=["Pilih"]))
        else:
            st.info("Tidak ada pesanan yang dipilih.")
    else:
        st.info("Tidak ada data pesanan yang ditemukan.")
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()

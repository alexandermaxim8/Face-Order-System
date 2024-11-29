import streamlit as st
import pandas as pd
from datetime import datetime
from navigation import make_sidebar
import fb_utils2 as fb

# Memanggil fungsi untuk membuat sidebar
make_sidebar()

st.title("🛒 Riwayat 10 Pesanan Terakhir")

# Memeriksa apakah pengguna telah login
if 'idToken' in st.session_state and 'email' in st.session_state:
    idToken = st.session_state['idToken']
    user = st.session_state['email']

    # Mengambil data maksimal limit=20 pesanan terakhir
    json_response = fb.get_recent_order(idToken, user, limit=20)

    if "document" in json_response[0]:
        orders = []
        for doc in json_response:
            fields = doc["document"]["fields"]
            order_time = datetime.fromisoformat(fields["datetime"]["timestampValue"].replace("Z", "+00:00"))
            order_items = [item["mapValue"]["fields"]["name"]["stringValue"] for item in fields["menu"]["arrayValue"]["values"]]
            total_price = sum(int(item["mapValue"]["fields"]["price"]["integerValue"]) for item in fields["menu"]["arrayValue"]["values"])
            orders.append({
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
            hide_index=True
            
        )

        # Menampilkan data pesanan yang dipilih
        selected_orders = edited_df[edited_df["Pilih"]]
        if not selected_orders.empty:
            st.subheader("Pesanan yang Dipilih")
            st.table(selected_orders.drop(columns=["Pilih"]))
        else:
            st.info("Tidak ada pesanan yang dipilih.")
    else:
        st.info("Tidak ada data pesanan yang ditemukan.")
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()

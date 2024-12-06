import streamlit as st
import cv2
import dlib
import numpy as np
import time
import os
from datetime import datetime, timezone, timedelta
import fb_utils2 as fb
from navigation import make_sidebar

# pastikan file shape_predictor_68_face_landmarks.dat tersedia di direktori yang sama
# atau sesuaikan path-nya
script_dir = os.path.dirname(os.path.abspath(__file__))
facial_landmark_file = os.path.join(script_dir, 'shape_predictor_68_face_landmarks.dat')

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(facial_landmark_file)

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

st.title("😊 Pemesanan Menggunakan Face Recognition")

# Fungsi perhitungan EAR (Eye Aspect Ratio)
def calculate_ear(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def pengambilan_gambar():
    start_time = time.time()
    video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    video.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    video.set(cv2.CAP_PROP_FPS, 20)
    video.set(cv2.CAP_PROP_BUFFERSIZE, 10)
    video.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    EAR_buffer = []
    blink_counter = 0
    liveness = False
    sudah_pencet = False
    font = cv2.FONT_HERSHEY_SIMPLEX
    frame_crop = None

    while True:
        ret, frame = video.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        x1, y1, x2, y2 = 0, 0, frame.shape[1], frame.shape[0]

        if faces:
            face = max(faces, key=lambda rect: rect.width() * rect.height())
            x1 = max(0, face.left() - face.width() // 20)
            y1 = max(0, face.top()- face.height() // 6)
            x2 = min(frame.shape[1], face.right() + face.width() // 20)
            y2 = min(frame.shape[0], face.bottom() + face.height() // 10)
            frame_crop = frame[int(y1):int(y2), int(x1):int(x2)]

            shape = predictor(gray, face)
            coords = np.array([[p.x, p.y] for p in shape.parts()])
            left_eye = coords[36:42]
            right_eye = coords[42:48]
            ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0

            if not sudah_pencet:
                EAR_buffer.append(ear)
                EAR_THRESHOLD1 = max(np.mean(EAR_buffer) - 2*np.std(EAR_buffer), 0.13)
                EAR_THRESHOLD2 = max(np.mean(EAR_buffer) + 0.5*np.std(EAR_buffer), 1.1*EAR_THRESHOLD1)

            if sudah_pencet:
                cv2.putText(frame, 'Silahkan kedip', (50, 100), font, 0.7, (0, 0, 255), 2)
                if ear < EAR_THRESHOLD1 and blink_counter <1:
                    blink_counter +=1
                elif blink_counter > 0 and ear >= EAR_THRESHOLD2:
                    # Kedipan terdeteksi
                    liveness = True
                    break
            else:
                cv2.putText(frame, 'Tekan huruf "c"', (50, 100), font, 0.7, (0, 0, 255), 2)
        else:
            cv2.putText(frame, 'Wajah tidak terdeteksi', (50, 100), font, 0.7, (0, 0, 255), 2)

        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, f'Kedipan: {blink_counter}', (10, 30), font, 0.7, (0, 0, 255), 2)
        cv2.imshow("Frame", frame)
        if frame_crop is not None:
            cv2.imshow("Frame Crop", frame_crop)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            sudah_pencet = True
            time.sleep(0.1)
        elif key == ord('q') or liveness:
            break

    video.release()
    cv2.destroyAllWindows()
    if liveness and frame_crop is not None:
        # Simpan foto (opsional)
        cv2.imwrite("captured_frame_crop.jpg", frame_crop)
        return True
    else:
        return False


# Logika Streamlit
if 'idToken' in st.session_state and 'email' in st.session_state:
    idToken = st.session_state['idToken']
    user = st.session_state['email']

    st.write("Silakan klik tombol di bawah untuk memulai face recognition.")
    if st.button("Mulai Face Recognition"):
        st.write("Membuka kamera... (Jendela baru akan muncul)")
        st.write("Tekan 'c' untuk konfirmasi, lalu kedip untuk verifikasi liveness. Tekan 'q' untuk keluar.")
        recognized = pengambilan_gambar()
        if recognized:
            st.success("Wajah terverifikasi. Menampilkan menu favorit Anda...")

            # Ambil menu favorit user (asumsikan telah tersedia fungsi get_favorites atau gunakan get_menu)
            # Di sini kita asumsikan get_favorites sudah dibuat
            # favorites = get_favorites(idToken, user)
            # Untuk contoh, kita pakai get_menu saja:
            favorites = fb.get_menu(idToken, user) # gantikan dengan get_favorites bila sudah ada
            fav_dict = {doc['fields']['name']['stringValue']: int(doc['fields']['price']['integerValue']) for doc in favorites}

            if fav_dict:
                st.subheader("Menu Favorit Anda")
                selected_items = {}
                for m_name, m_price in fav_dict.items():
                    qty = st.number_input(f"{m_name} - Rp{m_price}", min_value=0, step=1, key=m_name)
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
                        st.success("Pesanan Anda sedang diproses, tunggu sebentar!")

                        # Log menu ke Firestore
                        order_id = int(datetime.now().timestamp())
                        fb.log_menu(idToken, user, menu_array, order_id)
                        st.balloons()
            else:
                st.warning("Anda belum memiliki menu favorit.")
        else:
            st.warning("Face recognition gagal atau dibatalkan.")
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()

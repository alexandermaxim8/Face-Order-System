import streamlit as st
import cv2
import dlib
import numpy as np
import time
import os
from navigation import make_sidebar

# saat refresh website, maka akan kembali ke halaman login
def check_login():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("Anda belum login. Mengarahkan ke halaman login...")
        #st.experimental_rerun()
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

make_sidebar()

st.title("Webcam Face Recognition with EAR (Blink) Detection")
st.caption("Alex, Amar, Zidan, dan Satwika")

# Inisialisasi detector dan predictor
script_dir = os.path.dirname(os.path.abspath(__file__))
facial_landmark_file = os.path.join(script_dir, 'shape_predictor_68_face_landmarks.dat')
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(facial_landmark_file)

def calculate_ear(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# State variabel: kita simpan di session_state agar saat halaman rerun, state tetap ada
if 'sudah_pencet' not in st.session_state:
    st.session_state.sudah_pencet = False
if 'EAR_buffer' not in st.session_state:
    st.session_state.EAR_buffer = []
if 'blink_counter' not in st.session_state:
    st.session_state.blink_counter = 0
if 'liveness' not in st.session_state:
    st.session_state.liveness = False

if 'idToken' in st.session_state and 'email' in st.session_state:
    idToken = st.session_state['idToken']
    user = st.session_state['email']
        
# Tombol untuk memulai proses kedip (menggantikan 'c')
konfirmasi_pressed = st.button("Konfirmasi (Mulai Proses Kedip)")
if konfirmasi_pressed:
    st.session_state.sudah_pencet = True

# Tombol untuk menghentikan video
stop_button_pressed = st.button("Stop")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 20)

frame_placeholder = st.empty()

font = cv2.FONT_HERSHEY_SIMPLEX

# Koordinat default untuk kotak hijau (jika wajah tidak terdeteksi)
x1, y1, x2, y2 = 0, 0, 480, 480

while cap.isOpened() and not stop_button_pressed:
    ret, frame = cap.read()
    if not ret:
        st.write("Video Capture Ended")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    # Reset koordinat ke default setiap loop
    x1, y1, x2, y2 = 0, 0, frame.shape[1], frame.shape[0]

    if len(faces) > 0:
        # Pilih wajah terbesar
        face = max(faces, key=lambda rect: rect.width() * rect.height())
        x1 = max(0, face.left() - face.width() // 20)
        y1 = max(0, face.top() - face.height() // 6)
        x2 = min(frame.shape[1], face.right() + face.width() // 20)
        y2 = min(frame.shape[0], face.bottom() + face.height() // 10)
        
        shape = predictor(gray, face)
        coords = np.array([[p.x, p.y] for p in shape.parts()])
        left_eye = coords[36:42]
        right_eye = coords[42:48]
        ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0

        # Kumpulkan EAR jika belum konfirmasi
        if not st.session_state.sudah_pencet:
            st.session_state.EAR_buffer.append(ear)
            # Hitung threshold hanya jika sudah cukup data
            if len(st.session_state.EAR_buffer) > 5:
                EAR_THRESHOLD1 = max(np.mean(st.session_state.EAR_buffer) - 2*np.std(st.session_state.EAR_buffer), 0.13)
                EAR_THRESHOLD2 = max(np.mean(st.session_state.EAR_buffer) + 0.5*np.std(st.session_state.EAR_buffer), 1.1*EAR_THRESHOLD1)
            else:
                EAR_THRESHOLD1 = 0.13
                EAR_THRESHOLD2 = 0.2
            cv2.putText(frame, 'Tekan tombol "Konfirmasi" untuk mulai cek kedip', (10, 50), font, 0.7, (0,0,255), 2)
        else:
            # Sudah konfirmasi, cek kedip
            if len(st.session_state.EAR_buffer) > 5:
                EAR_THRESHOLD1 = max(np.mean(st.session_state.EAR_buffer) - 2*np.std(st.session_state.EAR_buffer), 0.13)
                EAR_THRESHOLD2 = max(np.mean(st.session_state.EAR_buffer) + 0.5*np.std(st.session_state.EAR_buffer), 1.1*EAR_THRESHOLD1)
            else:
                EAR_THRESHOLD1 = 0.13
                EAR_THRESHOLD2 = 0.2

            cv2.putText(frame, 'Silahkan kedip', (50, 100), font, 0.7, (0, 0, 255), 2)
            if ear < EAR_THRESHOLD1 and st.session_state.blink_counter < 1:
                st.session_state.blink_counter += 1
            elif st.session_state.blink_counter > 0 and ear >= EAR_THRESHOLD2:
                # Kedipan terdeteksi
                cv2.putText(frame, 'Kedipan terdeteksi!', (50, 140), font, 0.7, (0, 255, 0), 2)
                st.session_state.liveness = True

        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, f'Kedipan: {st.session_state.blink_counter}', (10, 30), font, 0.7, (0, 0, 255), 2)
    else:
        cv2.putText(frame, 'Wajah tidak terdeteksi', (50, 100), font, 0.7, (0, 0, 255), 2)

    # Konversi frame ke RGB untuk ditampilkan di Streamlit
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_placeholder.image(frame_rgb, channels="RGB")

    # Jika liveness sudah True, kita bisa stop atau lakukan tindakan lain
    if st.session_state.liveness:
        st.success("Kedipan terdeteksi! Liveness terkonfirmasi.")
        # Anda dapat menghentikan loop jika diinginkan
        # break
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()
    
cap.release()
cv2.destroyAllWindows()
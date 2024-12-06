import streamlit as st
import cv2
import dlib
import numpy as np
import time
import os
from navigation import make_sidebar

def check_login():
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("Anda belum login. Mengarahkan ke halaman login...")
        st.session_state.logged_in = False
        st.session_state.clear()
        st.switch_page("login.py")

# Panggil fungsi ini di awal halaman
check_login()

hide_navigation_style = """
    <style>
    [data-testid="stSidebarNav"] > ul:first-child {
        display: none;
    }
    body, .css-18e3th9, .stApp {
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        background-color: #FAFAFA;
    }
    h1, h2, h3, h4 {
        color: #333333;
        font-weight: 600;
    }
    .stButton>button {
        border-radius: 5px;
        background-color: #0099FF;
        color: #FFFFFF;
        border: none;
        font-weight: 600;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #007ACC;
    }
    .css-1cpxqw2 a {
        text-decoration: none;
        font-weight: 600;
    }
    .css-1cpxqw2 a:hover {
        text-decoration: underline;
    }
    .stAlert, .stError, .stWarning, .stSuccess, .stInfo {
        border-radius: 8px;
    }
    </style>
"""
st.markdown(hide_navigation_style, unsafe_allow_html=True)
make_sidebar()

st.title("Webcam Face Recognition with EAR (Blink) Detection")
st.write("Aplikasi ini mendeteksi kedip mata sebagai bukti **liveness**. Pastikan Anda mengizinkan akses kamera.")

script_dir = os.path.dirname(os.path.abspath(__file__))
facial_landmark_file = os.path.join(script_dir, 'shape_predictor_68_face_landmarks.dat')
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(facial_landmark_file)

def calculate_ear(eye):
    # Menghitung jarak Euclidean antara titik mata vertikal
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    # Menghitung jarak Euclidean antara titik mata horizontal
    C = np.linalg.norm(eye[0] - eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# Inisialisasi state
if 'sudah_pencet' not in st.session_state:
    st.session_state.sudah_pencet = False
if 'EAR_buffer' not in st.session_state:
    st.session_state.EAR_buffer = []
if 'blink_counter' not in st.session_state:
    st.session_state.blink_counter = 0
if 'liveness' not in st.session_state:
    st.session_state.liveness = False
if 'stop_clicked' not in st.session_state:
    st.session_state.stop_clicked = False

idToken = st.session_state.get('idToken')
user = st.session_state.get('email')

if idToken and user:
    with st.expander("Petunjuk Penggunaan"):
        st.markdown("""
        **Langkah-langkah:**
        1. Tunggu kamera menyala dan wajah Anda terdeteksi.
        2. Tekan tombol **"Konfirmasi (Mulai Proses Kedip)"** setelah beberapa detik agar sistem mengenali pola mata normal.
        3. Setelah dikonfirmasi, kedipkan mata di depan kamera.
        4. Jika kedip terdeteksi, Anda akan melihat pesan sukses.
        5. Tekan "Stop" untuk menghentikan, atau "Reset Proses" untuk memulai ulang proses dari awal.
        """)

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        konfirmasi_pressed = st.button("Konfirmasi (Mulai Proses Kedip)")
    with col2:
        stop_button_pressed = st.button("Stop")
    with col3:
        reset_button_pressed = st.button("Reset Proses")

    if konfirmasi_pressed:
        st.session_state.sudah_pencet = True

    if stop_button_pressed:
        st.session_state.stop_clicked = True

    if reset_button_pressed:
        # Reset semua state ke kondisi awal
        st.session_state.sudah_pencet = False
        st.session_state.EAR_buffer = []
        st.session_state.blink_counter = 0
        st.session_state.liveness = False
        st.session_state.stop_clicked = False
        # Tidak perlu rerun manual, penekanan tombol sudah memicu rerun otomatis

    frame_placeholder = st.empty()

    # Jika stop belum ditekan, kita mulai video capture
    if not st.session_state.stop_clicked:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 20)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        font = cv2.FONT_HERSHEY_SIMPLEX
        # Koordinat default untuk kotak hijau
        x1, y1, x2, y2 = 0, 0, cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)


        # Looping untuk menampilkan frame secara real-time sampai Stop ditekan atau video habis
        while cap.isOpened() and not st.session_state.stop_clicked:
            ret, frame = cap.read()
            if not ret:
                st.write("Video Capture Ended")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)

            x1, y1, x2, y2 = 0, 0, frame.shape[1], frame.shape[0]

            if faces:
                face = max(faces, key=lambda rect: rect.width() * rect.height())
                x1 = max(0, face.left() - face.width() // 20)
                y1 = max(0, face.top() - face.height() // 6)
                x2 = min(frame.shape[1], face.right() + face.width() // 20)
                y2 = min(frame.shape[0], face.bottom() + face.height() // 10)
                # Crop frame
                frame_crop = frame[int(y1):int(y2), int(x1):int(x2)]

                shape = predictor(gray, face)
                coords = np.array([[p.x, p.y] for p in shape.parts()])
                left_eye = coords[36:42]
                right_eye = coords[42:48]
                ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0

                if not st.session_state.sudah_pencet:
                    st.session_state.EAR_buffer.append(ear)
                    cv2.putText(frame, 'Tekan "Konfirmasi" untuk mulai cek kedip', (10, 50), font, 0.7, (0,0,255), 2)
                else:
                    EAR_THRESHOLD1 = max(np.mean(st.session_state.EAR_buffer) - 2*np.std(st.session_state.EAR_buffer), 0.13)
                    EAR_THRESHOLD2 = max(np.mean(st.session_state.EAR_buffer) + 0.5*np.std(st.session_state.EAR_buffer), 1.1*EAR_THRESHOLD1)
                    cv2.putText(frame, 'Silahkan kedip', (50, 100), font, 0.7, (0, 0, 255), 2)
                    
                    if ear < EAR_THRESHOLD1 and st.session_state.blink_counter < 1:
                        st.session_state.blink_counter += 1
                    
                    elif st.session_state.blink_counter > 0 and ear >= EAR_THRESHOLD2:
                        cv2.putText(frame, 'Kedipan terdeteksi!', (50, 140), font, 0.7, (0, 255, 0), 2)
                        st.session_state.liveness = True
                        cv2.imwrite("captured_frame.jpg", frame)
                        cv2.imwrite("captured_frame_crop.jpg", frame_crop)
                        st.success("Kedipan terdeteksi! Liveness terkonfirmasi.")
                        st.info("Tekan 'Stop' untuk menghentikan atau 'Reset Proses' untuk mencoba ulang.")

                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(frame, f'Kedipan: {st.session_state.blink_counter}', (10, 30), font, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(frame, 'Wajah tidak terdeteksi, coba mendekat/atur cahaya.', (20, 100), font, 0.7, (0, 0, 255), 2)

            # frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame, channels="BGR")

            # if st.session_state.liveness:
            #     st.success("Kedipan terdeteksi! Liveness terkonfirmasi.")
            #     st.info("Tekan 'Stop' untuk menghentikan atau 'Reset Proses' untuk mencoba ulang.")

            # Delay sedikit untuk mencegah penggunaan CPU berlebih
            cv2.waitKey(1)

        cap.release()
        cv2.destroyAllWindows()
    else:
        # Stop ditekan
        st.info("Proses dihentikan. Tekan 'Reset Proses' untuk memulai ulang.")
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()

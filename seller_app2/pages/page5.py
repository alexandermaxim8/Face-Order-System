import streamlit as st
import cv2
import dlib
import numpy as np
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

@st.cache_resource
def get_camera():
    # Fungsi ini hanya dipanggil sekali karena di-cache
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 20)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    return cap

def calculate_ear(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# Inisialisasi state jika belum ada
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
if 'EAR_THRESHOLD1' not in st.session_state:
    st.session_state.EAR_THRESHOLD1 = None
if 'EAR_THRESHOLD2' not in st.session_state:
    st.session_state.EAR_THRESHOLD2 = None
if 'messages' not in st.session_state:
    st.session_state.messages = []  # Untuk menyimpan pesan-pesan

idToken = st.session_state.get('idToken')
user = st.session_state.get('email')

if idToken and user:
    with st.expander("Petunjuk Penggunaan"):
        st.markdown("""
        **Langkah-langkah:**
        1. Tunggu kamera menyala dan wajah Anda terdeteksi.
        2. Tekan tombol **"Konfirmasi (Mulai Proses Kedip)"** setelah beberapa detik agar sistem mengenali pola mata normal.
        3. Setelah dikonfirmasi, kedipkan mata di depan kamera.
        4. Jika kedip terdeteksi, Anda akan melihat pesan sukses di kotak bawah.
        5. Tekan "Stop" untuk menghentikan, atau "Reset Proses" untuk memulai ulang proses dari awal (dan menghapus semua pesan).
        """)

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        konfirmasi_pressed = st.button("Konfirmasi (Mulai Proses Kedip)")
    with col2:
        stop_button_pressed = st.button("Stop")
    with col3:
        reset_button_pressed = st.button("Reset Proses")

    if konfirmasi_pressed:
        if len(st.session_state.EAR_buffer) < 5:
            st.session_state.messages.append("Data EAR belum cukup, tunggu beberapa detik sebelum menekan konfirmasi.")
        else:
            st.session_state.sudah_pencet = True
            mean_ear = np.mean(st.session_state.EAR_buffer)
            std_ear = np.std(st.session_state.EAR_buffer)
            st.session_state.EAR_THRESHOLD1 = max(mean_ear - 2 * std_ear, 0.13)
            st.session_state.EAR_THRESHOLD2 = max(mean_ear + 0.5 * std_ear, 1.1 * st.session_state.EAR_THRESHOLD1)
            st.session_state.messages.append("Proses kedip dikonfirmasi, silakan kedipkan mata di depan kamera.")

    if stop_button_pressed:
        st.session_state.stop_clicked = True
        st.session_state.messages.append("Proses dihentikan. Tekan 'Reset Proses' untuk memulai ulang.")

    if reset_button_pressed:
        st.session_state.sudah_pencet = False
        st.session_state.EAR_buffer = []
        st.session_state.blink_counter = 0
        st.session_state.liveness = False
        st.session_state.stop_clicked = False
        st.session_state.EAR_THRESHOLD1 = None
        st.session_state.EAR_THRESHOLD2 = None
        st.session_state.messages = []  # Hapus semua pesan

    frame_placeholder = st.empty()
    message_container = st.empty()

    if not st.session_state.stop_clicked:
        cap = get_camera()

        font = cv2.FONT_HERSHEY_SIMPLEX

        while cap.isOpened() and not st.session_state.stop_clicked:
            ret, frame = cap.read()
            if not ret:
                st.session_state.messages.append("Video Capture Ended")
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

                shape = predictor(gray, face)
                coords = np.array([[p.x, p.y] for p in shape.parts()])
                left_eye = coords[36:42]
                right_eye = coords[42:48]
                ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0

                if not st.session_state.sudah_pencet:
                    st.session_state.EAR_buffer.append(ear)
                else:
                    EAR_THRESHOLD1 = st.session_state.EAR_THRESHOLD1
                    EAR_THRESHOLD2 = st.session_state.EAR_THRESHOLD2

                    if ear < EAR_THRESHOLD1 and st.session_state.blink_counter < 1:
                        st.session_state.blink_counter += 1
                    elif st.session_state.blink_counter > 0 and ear >= EAR_THRESHOLD2:
                        if not st.session_state.liveness:
                            st.session_state.liveness = True
                            st.session_state.messages.append("Kedipan terdeteksi! Liveness terkonfirmasi.")

                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

            frame_placeholder.image(frame, channels="BGR")
            cv2.waitKey(1)

            # Tampilkan semua pesan dengan font lebih besar
            with message_container:
                if st.session_state.messages:
                    st.markdown("<h3 style='font-size:22px;'>Informasi:</h3>", unsafe_allow_html=True)
                    for msg in st.session_state.messages:
                        st.markdown(f"<p style='font-size:20px;'>{msg}</p>", unsafe_allow_html=True)
                else:
                    # Jika tidak ada pesan
                    st.markdown("<p style='font-size:20px;'> </p>", unsafe_allow_html=True)

        cap.release()
        cv2.destroyAllWindows()
    
    else:
        with message_container:
            if st.session_state.messages:
                st.markdown("<h3 style='font-size:22px;'>Informasi:</h3>", unsafe_allow_html=True)
                for msg in st.session_state.messages:
                    st.markdown(f"<p style='font-size:20px;'>{msg}</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size:20px;'>Proses dihentikan. Tekan 'Reset Proses' untuk memulai ulang.</p>", unsafe_allow_html=True)
else:
    st.error("Anda belum login. Silakan login terlebih dahulu.")
    st.stop()
cv2.destroyAllWindows()

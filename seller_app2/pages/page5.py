import streamlit as st
import cv2
import dlib
import numpy as np
import os
from navigation import make_sidebar
import base64
import io
import json
import requests
import fb_utils2 as fb
import time

def reset(super=False):
    st.session_state.sudah_pencet = False
    st.session_state.EAR_buffer = []
    st.session_state.blink_counter = 0
    st.session_state.liveness = False
    # st.session_state.stop_clicked = False
    st.session_state.EAR_THRESHOLD1 = None
    st.session_state.EAR_THRESHOLD2 = None
    st.session_state.messages = []  # Hapus semua pesan
    st.session_state.similar_face = False
    st.session_state.cam_active = True
    if super:
        keys_to_keep = ["guest_in", "logged_in", "email", "first_visit"]
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]

if 'first_visit_face' not in st.session_state:
    st.session_state.first_visit_face = True

if st.session_state.first_visit_face:
    reset(super=True)  # Clear everything except "guest_in"
    st.session_state.first_visit_face = False

def check_login():
    if 'guest_in' not in st.session_state or not st.session_state['guest_in']:
        st.warning("Anda belum login. Mengarahkan ke halaman login...")
        st.session_state.guest_in = False
        st.session_state.clear()
        st.switch_page("login.py")

# Panggil fungsi ini di awal halaman
check_login()
user = st.session_state.get('email')
url = "http://127.0.0.1:8000"

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

# @st.cache_resource
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
# if 'stop_clicked' not in st.session_state:
#     st.session_state.stop_clicked = False
if 'EAR_THRESHOLD1' not in st.session_state:
    st.session_state.EAR_THRESHOLD1 = None
if 'EAR_THRESHOLD2' not in st.session_state:
    st.session_state.EAR_THRESHOLD2 = None
if 'messages' not in st.session_state:
    st.session_state.messages = []  # Untuk menyimpan pesan-pesan
if 'cam_active' not in st.session_state:
    st.session_state.cam_active = True  # Untuk menyimpan pesan-pesan
if 'similar_face' not in st.session_state:
    st.session_state.similar_face = False  # Untuk menyimpan pesan-pesan
if 'not_found' not in st.session_state:
    st.session_state.not_found = False # Untuk menyimpan pesan-pesan
if 'response_face' not in st.session_state:
    st.session_state.response_face = None
if 'edit_fav' not in st.session_state:
    st.session_state.edit_fav = False

idToken = st.session_state.get('idToken')
user = st.session_state.get('email')

reset_button_pressed = st.button("Retake", type="primary")
if reset_button_pressed:
    reset(super=True)
    st.rerun()

if st.session_state.cam_active:
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
        konfirmasi_pressed = st.button("Start Blinking")
    # with col2:
    #     stop_button_pressed = st.button("Stop")
    # with col3:
        # reset_button_pressed = st.button("Reset Proses")

    # if st.session_state.similar_face:
    #     st.warning('Your face is already registered, please order via personalized favorite to edit or manually', icon="🚨")
    if st.session_state.not_found:
        st.error(f'An error occured: {st.session_state.response_face["error"]}. Please retake', icon="🚨")

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

    # if stop_button_pressed:
    #     st.session_state.stop_clicked = True
    #     st.session_state.messages.append("Proses dihentikan. Tekan 'Reset Proses' untuk memulai ulang.")

    # if reset_button_pressed:
    #     reset()

    frame_placeholder = st.empty()
    message_container = st.empty()

    # if not st.session_state.stop_clicked:
    cap = get_camera()

    font = cv2.FONT_HERSHEY_SIMPLEX

    while cap.isOpened():
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

            frame_crop = frame[int(y1):int(y2), int(x1):int(x2)]

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
                        time.sleep(1)
                        break

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

    with st.spinner('Recognizing your face'):
        retval, buffer = cv2.imencode('.jpg', frame_crop)
        image_bytes = buffer.tobytes()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        headers = {'Content-Type': 'application/json'}
        face = {"face": image_base64, "user": user}
        response = requests.post(f"{url}/predict", data=json.dumps(face), headers=headers) 

    if "error" in response.json():
        st.session_state.response_face = response.json()
        st.session_state.not_found = True
        reset()
        st.rerun()
    else:
        st.session_state.cam_active = False
        st.session_state.response_face = response.json()
        st.rerun()
    # else:
    #     with message_container:
    #         if st.session_state.messages:
    #             st.markdown("<h3 style='font-size:22px;'>Informasi:</h3>", unsafe_allow_html=True)
    #             for msg in st.session_state.messages:
    #                 st.markdown(f"<p style='font-size:20px;'>{msg}</p>", unsafe_allow_html=True)
    #         else:
    #             st.markdown("<p style='font-size:20px;'>Proses dihentikan. Tekan 'Reset Proses' untuk memulai ulang.</p>", unsafe_allow_html=True)
else:
    if st.session_state.edit_fav == False:
        if "menu_fav" not in st.session_state:
            menu_list = st.session_state.response_face["menu"]
            print(menu_list)
            st.session_state.menu_fav = {
                name: price 
                for name, price in zip(menu_list["name"], menu_list["price"])
            }

        menus = st.session_state.menu_fav
        st.subheader("Favorite Menu")

        selected_items = {}
        for m_name, m_price in menus.items():
            qty = st.number_input(f"{m_name} - Rp.{m_price}", min_value=0, step=1, key=m_name)
            if qty > 0:
                selected_items[m_name] = (m_price, qty)

        if st.button("Place Order", type="primary"):
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
                st.success("Your food is being cooked, wait and enjoy!")
                st.balloons()

                # Barulah di sini kita tulis ke Firebase
                # order_id = int(datetime.now().timestamp())
                id = st.session_state.response_face["match_id"]
                result = fb.log_menu(user, menu_array, id)
                if result:
                    st.write("Menu logged successfully!")
                    reset(super=True)
                    # st.rerun()
    
        if st.button("Edit Favorite", type="secondary"):
            st.session_state.edit_fav = True
            st.rerun()
            # Ambil data menu hanya saat pertama kali halaman dibuka atau saat tidak ada di session_state
        
    if st.session_state.edit_fav == True:
        if "menus2" not in st.session_state:
            st.session_state.menus2 = fb.get_menu(user)

        print(st.session_state.menus2)
        menus = {
                doc['fields']['name']['stringValue']: int(doc['fields']['price']['integerValue']) 
                for doc in st.session_state.menus2
            }
        print(menus)

        selected_items = {}
        menupick = []
        st.subheader("Edit Menu")

        # st.info("Silakan pilih menu secara manual dari daftar berikut:")
        for i, (m_name, m_price) in enumerate(menus.items()):
            qty = st.number_input(f"{m_name} - Rp.{m_price}", min_value=0, step=1, key=m_name)
            if qty > 0:
                selected_items[m_name] = (m_price, qty)
                menupick.append(i)
        
        if st.button("Edit & Order", type="primary"):
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
                st.success("Your food is being cooked, wait and enjoy!")
                st.balloons()

                # Barulah di sini kita tulis ke Firebase
                # order_id = int(datetime.now().timestamp())
                selected_menu = [st.session_state.menus2[x] for x in menupick]
                print(selected_menu)
                result1 = fb.add_user(st.session_state.response_face["match_id"], selected_menu, user)
                result2 = fb.log_menu(user, menu_array, 0)
                if result1 and result2:
                    st.write("Favorite menu updated & order logged successfully!")
                    # reset(super=True)
                    # st.rerun()

        if st.button("Cancel"):
            menu_list = fb.get_menu(user, st.session_state.response_face["match_id"])
            st.session_state.menu_fav = {
                name: price 
                for name, price in zip(menu_list["name"], menu_list["price"])
            }
            st.session_state.edit_fav = False
            st.rerun()

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
    st.cache_resource.clear()
    if super:
        keys_to_keep = ["guest_in", "logged_in", "email", "first_visit_face"]
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

@st.cache_resource
def get_camera():
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
if 'EAR_THRESHOLD1' not in st.session_state:
    st.session_state.EAR_THRESHOLD1 = None
if 'EAR_THRESHOLD2' not in st.session_state:
    st.session_state.EAR_THRESHOLD2 = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'cam_active' not in st.session_state:
    st.session_state.cam_active = True
if 'similar_face' not in st.session_state:
    st.session_state.similar_face = False
if 'not_found' not in st.session_state:
    st.session_state.not_found = False
if 'response_face' not in st.session_state:
    st.session_state.response_face = None
if 'edit_fav' not in st.session_state:
    st.session_state.edit_fav = False
if 'mode' not in st.session_state:
    st.session_state.mode = "Face Order"
if 'new_face' not in st.session_state:
    st.session_state.new_face = None
if 'order' not in st.session_state:
    st.session_state.order = True

idToken = st.session_state.get('idToken')
user = st.session_state.get('email')

reset_button_pressed = st.button("Retake", type="primary")
if reset_button_pressed:
    reset(super=True)
    st.rerun()

if st.session_state.cam_active:
    with st.expander("Petunjuk Penggunaan"):
        st.markdown("""
        **Langkah-langkah Penggunaan:**
        1. **Tunggu kamera menyala.** Pastikan wajah Anda terlihat jelas oleh kamera.
        2. **Pilih mode:**
        - **Face Order:** Pilih mode ini jika Anda sudah mendaftarkan wajah Anda sebelumnya untuk memesan menu favorit.
        - **Register New Face:** Pilih mode ini jika Anda belum pernah mendaftarkan wajah Anda.
        3. Klik tombol **"Start Blinking"** setelah beberapa detik agar sistem dapat mengenali pola mata Anda.
        4. Kedipkan mata Anda di depan kamera untuk memverifikasi kehadiran (liveness).
        5. Jika Anda ingin mengulang proses pengambilan foto, klik tombol **"Retake"**.
        6. **Mode Face Order:**
        - Setelah wajah dikenali, Anda dapat langsung memesan dari daftar menu favorit Anda.
        - Jika Anda ingin mengubah menu favorit, pilih **Edit Favorite** setelah mode Face Order aktif.
        7. **Mode Register New Face:**
        - Setelah pengenalan wajah selesai, pilih menu yang Anda ingin tambahkan ke favorit.
        - Pastikan untuk mengklik **Register & Order** untuk menyimpan data wajah dan menu favorit Anda.
        8. Jika ada kendala, Anda dapat kembali ke langkah sebelumnya dengan tombol "Retake".

        **Tips:**
        - Pastikan pencahayaan di sekitar Anda cukup agar kamera dapat mengenali wajah Anda dengan baik.
        - Jangan ragu untuk mengulang proses jika sistem gagal mendeteksi kedipan mata Anda.

        **Selamat memesan!**
        """)
    mode = st.radio("Choose Mode:", ["Face Order", "Register New Face"], key="mode")
    
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        konfirmasi_pressed = st.button("Start Blinking")

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

    frame_placeholder = st.empty()
    message_container = st.empty()

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

        with message_container:
            if st.session_state.messages:
                st.markdown("<h3 style='font-size:22px;'>Informasi:</h3>", unsafe_allow_html=True)
                for msg in st.session_state.messages:
                    st.markdown(f"<p style='font-size:20px;'>{msg}</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size:20px;'> </p>", unsafe_allow_html=True)

    cap.release()
    cv2.destroyAllWindows()

    if 'frame_crop' in globals():
        if st.session_state.mode == "Face Order":
            with st.spinner('Recognizing your face'):
                retval, buffer = cv2.imencode('.jpg', frame_crop)
                image_bytes = buffer.tobytes()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                headers = {'Content-Type': 'application/json'}
                face = {"face": image_base64, "user": user}
                response = requests.post(f"{url}/predict", data=json.dumps(face), headers=headers) 
                st.session_state.order = True

            if "error" in response.json():
                st.session_state.response_face = response.json()
                st.session_state.not_found = True
                reset()
                st.rerun()
            else:
                st.session_state.cam_active = False
                st.session_state.response_face = response.json()
                st.rerun()
        
        elif st.session_state.mode == "Register New Face":
            with st.spinner('Capturing your face'):
                retval, buffer = cv2.imencode('.jpg', frame_crop)
                image_bytes = buffer.tobytes()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                st.session_state.new_face = image_base64
                st.session_state.cam_active = False
                st.session_state.order = False
                st.rerun()

elif (not st.session_state.cam_active) and st.session_state.order:
    # Pada kondisi Face Order setelah camera off (liveness terkonfirmasi) dan order = True
    # Tampilkan menu favorit dengan jumlah 1 tiap menu tanpa plus-minus
    if st.session_state.edit_fav == False:
        if "menu_fav" not in st.session_state:
            menu_list = st.session_state.response_face["menu"]
            st.session_state.menu_fav = {
                name: price 
                for name, price in zip(menu_list["name"], menu_list["price"])
            }

        menus = st.session_state.menu_fav
        st.subheader("Favorite Menu")

        # Tampilkan langsung quantity=1 tanpa number_input
        total = 0
        menu_array = []
        for m_name, m_price in menus.items():
            qty = 1
            subtotal = m_price * qty
            st.write(f"{m_name} x {qty} - Rp.{subtotal}")
            total += subtotal
            menu_array.append({
                "mapValue": {
                    "fields": {
                        "name": {"stringValue": m_name},
                        "price": {"integerValue": str(m_price)},
                        "quantity": {"integerValue": str(qty)}
                    }
                }
            })

        st.write(f"**Total: Rp.{total}**")

        if st.button("Place Order", type="primary"):
            st.success("Your food is being cooked, wait and enjoy!")
            st.balloons()
            id = st.session_state.response_face["match_id"]
            result = fb.log_menu(user, menu_array, id)
            if result:
                st.write("Menu logged successfully!")
                reset(super=True)

        if st.button("Edit Favorite", type="secondary"):
            st.session_state.edit_fav = True
            st.rerun()

    if st.session_state.edit_fav == True:
        if "menus" not in st.session_state:
            menu_list = fb.get_menu(user)
            st.session_state.menus = {
                doc['fields']['name']['stringValue']: int(doc['fields']['price']['integerValue']) 
                for doc in menu_list
            }
            # Simpan menus2 untuk indexing saat edit
            st.session_state.menus2 = menu_list

        menus = st.session_state.menus

        st.subheader("Edit Menu")

        # Di mode edit, gunakan form + number_input dengan max_value=1
        with st.form("edit_fav_form"):
            selected_items = {}
            menupick = []
            for i, (m_name, m_price) in enumerate(menus.items()):
                # max_value=1 agar tidak bisa lebih dari 1
                qty = st.number_input(f"{m_name} - Rp.{m_price}", min_value=0, max_value=1, step=1, key=f"edit_{m_name}")
                if qty > 0:
                    selected_items[m_name] = (m_price, qty)
                    menupick.append(i)
            
            submit_edit_order = st.form_submit_button("Edit & Order", type="primary")

        if submit_edit_order:
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

                if "menus2" not in st.session_state:
                    menu_list = fb.get_menu(user)
                    st.session_state.menus2 = menu_list

                selected_menu = [st.session_state.menus2[x] for x in menupick]
                result1 = fb.add_user(st.session_state.response_face["match_id"], selected_menu, user)
                result2 = fb.log_menu(user, menu_array, 0)
                if result1 and result2:
                    st.write("Favorite menu updated & order logged successfully!")

        if st.button("Go Back"):
            menu_list = fb.get_menu(user, st.session_state.response_face["match_id"])
            st.session_state.menu_fav = {
                name: price 
                for name, price in zip(menu_list["name"], menu_list["price"])
            }
            st.session_state.edit_fav = False
            st.rerun()

elif (not st.session_state.cam_active) and (not st.session_state.order):
    # Kondisi Register New Face setelah kamera mati dan order = False
    # Di mode ini gunakan max_value=1 pada number_input juga
    if "menus2" not in st.session_state:
        menu_list2 = fb.get_menu(user)
        st.session_state.menus2 = menu_list2
    if "menus" not in st.session_state:
        st.session_state.menus = {
            doc['fields']['name']['stringValue']: int(doc['fields']['price']['integerValue']) 
            for doc in st.session_state.menus2
        }

    menus = st.session_state.menus
    
    st.subheader("Edit Menu (Register New Face)")

    with st.form("register_order_form"):
        selected_items = {}
        menupick = []
        for i, (m_name, m_price) in enumerate(menus.items()):
            # max_value=1 disini juga
            qty = st.number_input(f"{m_name} - Rp.{m_price}", min_value=0, max_value=1, step=1, key=f"reg_{m_name}")
            if qty > 0:
                selected_items[m_name] = (m_price, qty)
                menupick.append(i)
        
        submit_register = st.form_submit_button("Register & Order", type="primary")

    if submit_register:
        if len(selected_items) == 0:
            st.error("Anda belum memilih menu apapun!")
        else:
            headers = {'Content-Type': 'application/json'}
            selected_menu = [st.session_state.menus2[x] for x in menupick]
            face = {"menu": selected_menu, "face": st.session_state.new_face, "user": user}
            response = requests.post(f"{url}/train", data=json.dumps(face), headers=headers) 
            if "similar face" in response.json().get("status",""):
                st.warning('Your face is already registered, please order via personalized favorite to edit or manually', icon="🚨")
            elif "error" in response.json():
                st.error(f'An error occured: {response.json()["error"]}. Please retake', icon="🚨")
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
                st.success("Successfully registered. Your food is being cooked, wait and enjoy!")
                st.balloons()
                
                result = fb.log_menu(user, menu_array, response.json()["new_id"])
                if result:
                    st.write("Favorite menu updated & order logged successfully!")

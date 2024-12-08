import requests
import json
import ast
import cv2
import base64
import fb_utils as fb
import os
import time
import numpy as np
import dlib
from collections import Counter

import RPi.GPIO as GPIO
import i2clcd

# DEFINE BUTTON
UP_BUTTON = 26
DOWN_BUTTON = 19
ENTER_BUTTON = 13
CANCEL_BUTTON = 6
VIEW_BUTTON = 5

GPIO.setmode(GPIO.BCM)
GPIO.setup(UP_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DOWN_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ENTER_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(CANCEL_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VIEW_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# DEFINE LCD
lcd = i2clcd.i2clcd(i2c_bus=1, i2c_addr=0x27, lcd_width=20)
lcd.init()
items_per_page = 3

# DEFINE CUSTOM CHARACTER
panah = [0x02,0x06,0x0E,0x1E,0x1E,0x0E,0x06,0x02]
panah_atas = [0x00,0x00,0x04,0x0E,0x1F,0x00,0x00,0x00]
panah_bawah = [0x00,0x00,0x00,0x1F,0x0E,0x04,0x00,0x00]
rp = [0x1C,0x14,0x18,0x14,0x03,0x05,0x07,0x04]


lcd.write_CGRAM(panah, 0)
lcd.write_CGRAM(panah_atas, 1)
lcd.write_CGRAM(panah_bawah, 2)
lcd.write_CGRAM(rp, 3)


config = {
  "apiKey": "AIzaSyAy-FlE4rL-V2BwJ8oZEVhqiMY3qfqcQsA",
  "authDomain": "firestore-despro.firebaseapp.com",
  "databaseURL": "https://firestore-despro-default-rtdb.firebaseio.com",
  "projectId": "firestore-despro",
  "storageBucket": "firestore-despro.appspot.com",
  "messagingSenderId": "290267621401",
  "appId": "1:290267621401:web:9bad4a9b502013fd96a288",
  "measurementId": "G-DFY4Z6HJJG",
  "firestore_url": "https://firestore.googleapis.com"
}

auth = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={config["apiKey"]}'
auth_headers = {"Content-Type": "application/json"}


# email = "admin@gmail.com"
# password = "admin12345"

email = "alexandermaxim8@gmail.com"
password = "alex12345"
# url = "https://2174-139-255-78-2.ngrok-free.app"
# url = "https://e311-180-243-10-170.ngrok-free.app"
url = "http://127.0.0.1:8000"

# data = {"email": email, "password": password, "returnSecureToken": True}
# try:
#   response = requests.post(auth, data=json.dumps(data), headers=auth_headers)
#   response.raise_for_status()
#   json_response = response.json()
#   idToken = json_response["idToken"]
#   refreshToken = json_response["refreshToken"]

# except Exception as e:
#   print(f"An error occurred: {e}")
# else:
#   break
token = fb.init_firebase(email, password)
idToken = token["idToken"]
refreshToken = token["refreshToken"]
print("idToken:\n", idToken)

firestore_header = {
    "Authorization": f"Bearer {idToken}",
    "Content-Type": "application/json"
}




detector = dlib.get_frontal_face_detector()
script_dir = os.path.dirname(os.path.abspath(__file__))
facial_landmark_file=   os.path.join(script_dir,'shape_predictor_68_face_landmarks.dat')
print("facial landmark file ",facial_landmark_file)
predictor = dlib.shape_predictor(facial_landmark_file)  
# windows
def calculate_ear(eye):
    # Menghitung jarak Euclidean antara titik mata vertikal
    A = np.linalg.norm(eye[1] - eye[5])
    B =  np.linalg.norm(eye[2] - eye[4])

    # Menghitung jarak Euclidean antara titik mata horizontal
    C = np.linalg.norm(eye[0] - eye[3])

    # Menghitung EAR
    ear = (A + B) / (2.0 * C)
    return ear

def pengambilan_gambar():
    start_time = time.time()
    # video = cv2.VideoCapture(0, cv2.CAP_DSHOW)      # windows 
    video = cv2.VideoCapture(0, cv2.CAP_V4L2)      # linux
    video.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
    video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    video.set(cv2.CAP_PROP_FPS, 20)
    video.set(cv2.CAP_PROP_BUFFERSIZE, 10)
    video.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    print("Waktu membuka kamera:", time.time() - start_time)
    print("WIDTH, HEIGHT, FPS:", video.get(cv2.CAP_PROP_FRAME_WIDTH),
          video.get(cv2.CAP_PROP_FRAME_HEIGHT), video.get(cv2.CAP_PROP_FPS))

    EAR_THRESHOLD = 0.1
    EAR_buffer = []
    blink_counter = 0
    liveness = False
    sudah_pencet = False
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Koordinat default untuk kotak hijau
    x1, y1, x2, y2 = 0, 0, video.get(cv2.CAP_PROP_FRAME_WIDTH), video.get(cv2.CAP_PROP_FRAME_HEIGHT)

    while True:
        ret, frame = video.read()
        clear_screen()
        text = "Kamera Terbuka"
        lcd.move_cursor(1,10-len(text)//2)
        lcd.print(text)

        if not ret:
            text = "Kamera ditutup"
            lcd.move_cursor(1,10-len(text)//2)
            lcd.print(text)
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        if faces:
            # Memilih wajah dengan area terbesar
            face = max(faces, key=lambda rect: rect.width() * rect.height())

            # Menghitung koordinat dengan margin
            x1 = max(0, face.left() - face.width() // 20)
            y1 = max(0, face.top()- face.height() // 6)
            x2 = min(frame.shape[1], face.right() + face.width() // 20)
            y2 = min(frame.shape[0], face.bottom() + face.height() // 10)

            # Crop frame
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
                
            #print(f"{ear} {EAR_THRESHOLD1} {EAR_THRESHOLD2}")

            time.sleep(0.01)

            if sudah_pencet:
                cv2.putText(frame, 'Silahkan kedip', (50, 100), font,
                            0.7, (0, 0, 255), 2)

                # if ear < 0.05:
                #     blink_counter += 1
                # elif blink_counter > 0 and ear > 0.17:
                if ear < EAR_THRESHOLD1 and blink_counter <1:
                    blink_counter +=1

                elif blink_counter > 0 and ear >= EAR_THRESHOLD2:
                    print("Kedipan terdeteksi!")
                    cv2.imwrite("captured_frame.jpg", frame)
                    cv2.imwrite("captured_frame_crop.jpg", frame_crop)
                    liveness = True
                    break
                prev_ear = ear
            else:
                cv2.putText(frame, 'Tekan huruf "c"', (50, 100), font,
                            0.7, (0, 0, 255), 2)
                clear_screen()
                text = 'Tekan Tombol "Y"'
                lcd.move_cursor(1,10-len(text)//2)
                lcd.print(text)
                
        else:
            # Jika wajah tidak terdeteksi, gunakan koordinat default
            frame_crop = None
            cv2.putText(frame, 'Wajah tidak terdeteksi', (50, 100), font,
                        0.7, (0, 0, 255), 2)
            clear_screen()
            text = ["Wajah tidak", "terdeteksi"]
            lcd.move_cursor(1,10-len(text[0])//2)
            lcd.print(text[0])
            lcd.move_cursor(1,10-len(text[1])//2)
            lcd.print(text[1])

        # Gambar kotak hijau (selalu ditampilkan)
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

        cv2.putText(frame, f'Kedipan: {blink_counter}', (10, 30),
                    font, 0.7, (0, 0, 255), 2)
        cv2.imshow("Frame", frame)
        if frame_crop is not None:
            cv2.imshow("Frame Crop", frame_crop)

        # key = cv2.waitKey(1) & 0xFF
        if GPIO.input(ENTER_BUTTON) == GPIO.LOW:
            sudah_pencet = True
            time.sleep(0.1)
        # elif key == ord('q') or liveness:
        #     break
        elif liveness:
            clear_screen()
            text = "Kamera ditutup"
            lcd.move_cursor(1,10-len(text)//2)
            lcd.print(text)
            break

    video.release()
    cv2.destroyAllWindows()
    return frame_crop if 'frame_crop' in locals() else None

# DISPLAYING TO LCD
#===============================================
def clear_screen():
    lcd.clear()

def Count_list(my_list):
    result_counter = dict(Counter(my_list))
    return result_counter

def menu_selector(menu_items):
    global selected_index, current_index, max_index
    current_index = 0
    selected_index = 0
    max_index = len(menu_items)
    order_counts = {item: 0 for item in menu_items}  # Dictionary to store counts for each menu item
    # items_per_page = 4  # Limit items displayed per page
    
    time.sleep(0.2)
    def display_menu():
        lcd.clear()
        text = "Pilih Menu"
        lcd.move_cursor(0,10-len(text)//2)
        lcd.print(text)
        for i in range(3):
            if current_index + i < len(menu_items):
                menu = menu_items[current_index + i][0]
                price = str(menu_items[current_index + i][1])+"k"
                if i == selected_index:
                    menu_with_arrow = menu
                    lcd.print_line(menu_with_arrow+" "+chr(3)+ price, i+1)
                    lcd.move_cursor(i+1, 19)
                    lcd.print(chr(0)) 
                else:
                    menu_with_arrow = menu
                    lcd.print_line(menu_with_arrow+" "+chr(3)+ price, i+1)
                    

    def scroll_up():
        global selected_index, current_index
        if selected_index > 0:
            selected_index -= 1
        elif current_index > 0:
            current_index -= 3
            selected_index = 2

    def scroll_down():
        global selected_index, current_index, max_index
        if selected_index < 2:
            selected_index += 1
        elif current_index < max_index: 
            current_index += 3
            selected_index = 0

    def display_order_list(order_counts):
        clear_screen()
        # lcd.print_line("Your Current Order:", 0)
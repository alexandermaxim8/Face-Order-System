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
#url = "http://127.0.0.1:8000"
#url = "https://4976-103-177-96-64.ngrok-free.app"
url = "https://raspi.loca.lt"

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
    video = cv2.VideoCapture(0, cv2.CAP_V4L2)
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
        if not ret:
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
                
        else:
            # Jika wajah tidak terdeteksi, gunakan koordinat default
            frame_crop = None
            cv2.putText(frame, 'Wajah tidak terdeteksi', (50, 100), font,
                        0.7, (0, 0, 255), 2)

        # Gambar kotak hijau (selalu ditampilkan)
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

        cv2.putText(frame, f'Kedipan: {blink_counter}', (10, 30),
                    font, 0.7, (0, 0, 255), 2)
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
    max_index = len(menu_items[0])
    order_counts = {item[0]: 0 for item in menu_items}  # Dictionary to store counts for each menu item
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
        menupick = []
        # Prepare a list of items with counts
        order_list = [f"{item}: {count}" for item, count in order_counts.items() if count > 0]
        total_items = len(order_list)

        if total_items == 0:
            clear_screen()
            lcd.print_line("No items in the Cart", 1)
            time.sleep(1)
            return


        # Handle paging
        current_page = 0
        while True:
            start_index = current_page * items_per_page
            end_index = min(start_index + items_per_page, total_items)

            # Display items on the current page
            clear_screen()
            lcd.print_line("Your Current Order:",line=0)
            for idx, item in enumerate(order_list[start_index:end_index]):
                lcd.print_line(f" {item}", idx+1)

            # lcd.print()(f"{current_page + 1}/{(total_items - 1) // items_per_page + 1}")
            # print("Use 'up'/'down' to navigate, 'l' to exit.")
            max_page = (total_items - 1) // items_per_page + 1
            if current_page + 1 == 1 and total_items > 3:
                lcd.move_cursor(3,19)
                lcd.print(chr(2))
            elif current_page + 1 == max_page and total_items > 3:
                lcd.move_cursor(2,19)
                lcd.print(chr(1))
            elif current_page + 1 != 1 and current_page + 1 != max_page:
                lcd.move_cursor(2,19)
                lcd.print(chr(1))
                lcd.move_cursor(3,19)
                lcd.print(chr(2))
            
            time.sleep(0.2)
            while True:
                if GPIO.input(UP_BUTTON) == GPIO.LOW and current_page > 0:
                    current_page -= 1
                    time.sleep(0.2)
                    break
                elif GPIO.input(DOWN_BUTTON) == GPIO.LOW and end_index < total_items:
                    current_page += 1
                    time.sleep(0.2)
                    break
                elif GPIO.input(VIEW_BUTTON) == GPIO.LOW:
                    return
    display_menu()
    while True:
        

        # Wait for a key press
        if GPIO.input(UP_BUTTON) == GPIO.LOW:
            scroll_up()
            display_menu()
            time.sleep(0.2)
        elif GPIO.input(DOWN_BUTTON) == GPIO.LOW:
            scroll_down()
            display_menu()
            time.sleep(0.2)
        elif GPIO.input(ENTER_BUTTON) == GPIO.LOW:
            print(order_counts.keys())
            print(menu_items)
            print(current_index)
            print(selected_index)
            order_counts[menu_items[current_index+selected_index][0]] += 1  # Increment the count for the selected item
            clear_screen()
            lcd.print_line(f"Added {menu_items[current_index+selected_index][0]}",1)
            time.sleep(1)
            display_menu()
        elif GPIO.input(VIEW_BUTTON) == GPIO.LOW:
            display_order_list(order_counts)  # Display the current order list
            display_menu()
            time.sleep(0.2)
        elif GPIO.input(CANCEL_BUTTON) == GPIO.LOW:
            return order_counts  # Return the final counts when "y" is pressed
        
def display_final_order(order_counts, price):
    clear_screen()
    price = f"{price:,}".replace(",", ".")
    lcd.print_line("Your Final Order:", 0)

    # Prepare a list of items with counts
    order_list = [f"{item}: {count}" for item, count in order_counts.items() if count > 0]
    total_items = len(order_list)

    if total_items == 0:
        lcd.print_line("No items ordered.",1)
        time.sleep(2)
        return "cancel"

    # Handle paging
    current_page = 0
    while True:
        start_index = current_page * items_per_page
        end_index = min(start_index + items_per_page, total_items)

        # Display items on the current page
        clear_screen()
        lcd.print_line("Your Final Order",0)
        for idx, item in enumerate(order_list[start_index:end_index]):
            lcd.print_line(f" {item}",idx+1)

        # lcd.print_line(f"\nPage {current_page + 1}/{(total_items - 1) // items_per_page + 1}")
        max_page = (total_items - 1) // items_per_page + 1
        if current_page + 1 == 1 and total_items > 3:
            lcd.move_cursor(3,19)
            lcd.print(chr(2))
        elif current_page + 1 == max_page and total_items > 3:
            lcd.move_cursor(2,19)
            lcd.print(chr(1))
        elif current_page + 1 != 1 and current_page + 1 != max_page:
            lcd.move_cursor(2,19)
            lcd.print(chr(1))
            lcd.move_cursor(3,19)
            lcd.print(chr(2))
        # print("Press 'p' to proceed, 'c' to cancel, or 'e' to edit your order.")
        # print("Use 'up'/'down' to navigate pages.")
        

        while True:
            if GPIO.input(UP_BUTTON) == GPIO.LOW and current_page > 0:
                current_page -= 1
                time.sleep(0.2)
            elif GPIO.input(DOWN_BUTTON) == GPIO.LOW and end_index < total_items:
                current_page += 1
                time.sleep(0.2)
            elif GPIO.input(ENTER_BUTTON) == GPIO.LOW:
                text = "Checkout"
                lcd.move_cursor(0, 10-len(text)//2)
                lcd.print(text)
                lcd.move_cursor(1,0)
                lcd.print("Total: "+chr(3)+price)
                lcd.print_line("Proceed? [Y/E/X]", line=2)
                time.sleep(0.2)
                while True:
                    if GPIO.input(ENTER_BUTTON) == GPIO.LOW:
                        return "proceed"
                    elif GPIO.input(CANCEL_BUTTON) == GPIO.LOW:
                        return "cancel"
                    elif GPIO.input(VIEW_BUTTON) == GPIO.LOW:
                        return "edit"
            

def select_menu():
    menu = fb.get_menu(idToken, email)
    menu_list = []
    # menu = fb.get_menu(idToken, email)
    for i, menu_pilihan in enumerate(menu):
        # print(f'{i+1}. {menu_pilihan["fields"]["name"]["stringValue"]} - Rp.{menu_pilihan["fields"]["price"]["integerValue"]}')
        name = menu_pilihan["fields"]["name"]["stringValue"]
        price = int(menu_pilihan["fields"]["price"]["integerValue"]) / 1000
        menu_list.append([name, price])
    
    selected_order_counts = menu_selector(menu_list)
    # while True:
    #     try:
    #         print("Pick your favorites!\neg: 3 2 1")
    #         menupick = input(">> ")
    #         menupick = list(map(int, menupick.split(' ')))
    #         # Check if all selections are valid
    #         # selected_menu = [menu[x-1] for x in menupick]  # This will raise IndexError if an invalid index is chosen
    #         break  
    #     except IndexError:
    #         print("Invalid menu selection. Please enter valid menu numbers.")
    #     except ValueError:
    #         print("Invalid input. Please enter numbers only, separated by commas.")
    menupick = [
        index + 1
        for index, (key, value) in enumerate(selected_order_counts.items())
        for _ in range(value)  # Repeat based on value
        if value > 0
    ]
    print(menupick)
    print(menu)
    return menupick, menu, selected_order_counts

def order():
    response = None
    try:
        img = pengambilan_gambar()
        # img = cv2.imread("orang3.jpg", cv2.COLOR_BGR2RGB)
        retval, buffer = cv2.imencode('.jpg', img)
        image_bytes = buffer.tobytes()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        headers = {'Content-Type': 'application/json'}
        face = {"face": image_base64, "user": email, "token":idToken}
        response = requests.post(f"{url}/predict", data=json.dumps(face), headers=headers) 
        print("Rasberry Pi")
        print("berhasil request prediction")
        price = 0
        total_price = 0
        # Access the menu data
        if response.json() == {"error": "No match found"}:
            print("No match found. Please register first.")
            clear_screen()
            text = ["No match found", "Please Register"]
            lcd.move_cursor(1, 10-len(text[0])//2)
            lcd.print(text[0])
            lcd.move_cursor(1, 10-len(text[1])//2)
            lcd.print(text[1])
            time.sleep(1)
            return
        menu_data = response.json()["menu"]
        
        print("menu_dataU:", menu_data)
        # print("response:", response.json())
        # print("\nmenu_data :", menu_data)
        order_counts = menu_data["name"]
        # Loop through each menu item by index
        for i, (name, price_str) in enumerate(zip(menu_data["name"], menu_data["price"])):
            print(f'{i+1}. {name} - Rp.{price_str}')
            
            # Accumulate the total price, converting price_str to an integer
            total_price += int(price_str)

            
        # # Accumulate the price, converting price_str to an integer
        # price += int(price_str)
        # for i, menu_pilihan in enumerate(response.json()["menu"]):
        #   print(f'{i+1}. {menu_pilihan["fields"]["name"]["stringValue"]} - Rp.{menu_pilihan["fields"]["price"]["integerValue"]}')
        #   price += int(menu_pilihan[i-1]["fields"]["price"]["integerValue"])

        action = display_final_order(order_counts, total_price)
        if action == "proceed":
            clear_screen()
            lcd.move_cursor(1, 10-len(text[0])//2)
            lcd.print(text[0])
            time.sleep(1)

            clear_screen()
            lcd.move_cursor(1, 10-len(text[1])//2)
            lcd.print(text[1])
            lcd.move_cursor(2, 10-len(text[2])//2)
            lcd.print(text[2])
            time.sleep(2)
            selected_menu = [{"mapValue":{"fields":{"name":{"stringValue": menu_name}, "price":{"integerValue": menu_price}}}} for menu_name, menu_price in zip(menu_data["name"], menu_data["price"])]
            fb.log_menu(idToken, email, selected_menu, response.json()["match_id"])
            # return
        elif action == "cancel":
            clear_screen()
            lcd.move_cursor(1, 10-len(text[3])//2)
            lcd.print(text[3])
            time.sleep(1)
            # return
        elif action == "edit":
            while True:
                menupick, menu, order_counts = select_menu()
                price = 0
                for i in menupick:
                    print(f'{menu[i-1]["fields"]["name"]["stringValue"]} - Rp.{menu[i-1]["fields"]["price"]["integerValue"]}')
                    price += int(menu[i-1]["fields"]["price"]["integerValue"])
                    print(f"Total: {price}")
                clear_screen()
                text="Menu Updated"
                lcd.move_cursor(1,10-len(text)//2)
                lcd.print(text)
                time.sleep(1)
                text = ["Thank You", "Your Order", "is being Processed", "Order cancelled"]
                action = display_final_order(order_counts, price)
                if action == "proceed":
                    clear_screen()
                    lcd.move_cursor(1, 10-len(text[0])//2)
                    lcd.print(text[0])
                    time.sleep(1)

                    clear_screen()
                    lcd.move_cursor(1, 10-len(text[1])//2)
                    lcd.print(text[1])
                    lcd.move_cursor(2, 10-len(text[2])//2)
                    lcd.print(text[2])
                    selected_menu = [{"mapValue":{"fields":{"name":{"stringValue": menu[x-1]["fields"]["name"]["stringValue"]}, "price":{"integerValue": menu[x-1]["fields"]["price"]["integerValue"]}}}} for x in menupick]
                    fb.log_menu(idToken, email, selected_menu, response.json()["match_id"])
            
                    time.sleep(2)
                    break
                elif action == "cancel":
                    clear_screen()
                    lcd.move_cursor(1, 10-len(text[3])//2)
                    lcd.print(text[3])
                    time.sleep(1)
                    break
                elif action == "edit":
                    continue
        
    except requests.exceptions.RequestException as e:
        print("Error during order processing:", e)
        if response:
            print("Response text:", response.text)
            clear_screen()
            lcd.print_line("Error in the Backend",1)
            time.sleep(1)
            text = "Press any button"
            lcd.move_cursor(2,10-len(text)//2)
            lcd.print(text)
            while True:
                if GPIO.input(ENTER_BUTTON) == GPIO.LOW:
                    return
                elif GPIO.input(CANCEL_BUTTON) == GPIO.LOW:
                    return
                elif GPIO.input(UP_BUTTON) == GPIO.LOW:
                    return
                elif GPIO.input(DOWN_BUTTON) == GPIO.LOW:
                    return
                elif GPIO.input(VIEW_BUTTON) == GPIO.LOW:
                    return
    # finally:
    #     input("Press Enter to continue...")
    
def register():
    response = None
    try:
        menupick, menu, order_list = select_menu()
        selected_menu = [menu[x-1] for x in menupick]
        
        print("Get ready to take a picture.")
        clear_screen()
        text = "Membuka Kamera"
        lcd.move_cursor(1,10-len(text)//2)
        lcd.print(text)
        img = pengambilan_gambar()
        # img = cv2.imread("orang2.jpg", cv2.COLOR_BGR2RGB)
        retval, buffer = cv2.imencode('.jpg', img)
        image_bytes = buffer.tobytes()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        headers = {'Content-Type': 'application/json'}


        face = {"menu": selected_menu, "face": image_base64, "user": email, "token":idToken}
        response = requests.post(f"{url}/train", data=json.dumps(face), headers=headers) 
        response.raise_for_status()
        print("Registration response:", response.text)
        if "similar face" in response.json().get("status",""):
            text=("User","sudah diregister", "Balik ke Menu Utama")
            clear_screen()
            lcd.move_cursor(1,10-len(text[0])//2)
            lcd.print(text[0])
            lcd.move_cursor(2,10-len(text[1])//2)
            lcd.print(text[1])
            clear_screen()
            lcd.move_cursor(1,10-len(text[2])//2)
            lcd.print(text[2])
            return
        elif "error" in response.json():
            print(f'An error occured: {response.json()["error"]}')
            clear_screen()
            lcd.print_line("Error in the Backend",1)
        else:
            total_price = sum(int(menu[x-1]["fields"]["price"]["integerValue"]) for x in menupick)
            clear_screen()
            lcd.print_line(f"Total: Rp.{total_price}",1)
            time.sleep(2)

            text=("Your food is","being cooked", "Please Wait and", "Enjoy")
            lcd.move_cursor(1,10-len(text[0])//2)
            lcd.print(text[0])
            lcd.move_cursor(2,10-len(text[1])//2)
            lcd.print(text[1])
            time.sleep(1)
            lcd.move_cursor(1,10-len(text[2])//2)
            lcd.print(text[2])
            lcd.move_cursor(2,10-len(text[3])//2)
            lcd.print(text[3])
            time.sleep(1)
            # selected_menu = [menu["name"] for menu in selected_menu]
            selected_menu = [{"mapValue":{"fields":{"name":{"stringValue": menu[x-1]["fields"]["name"]["stringValue"]}, "price":{"integerValue": menu[x-1]["fields"]["price"]["integerValue"]}}}} for x in menupick]
            fb.log_menu(idToken, email, selected_menu, response.json()["new_id"])

    except requests.exceptions.ConnectionError as e:    
        print("Error during order processing:", e)
        clear_screen()
        text = "Connection Error"
        lcd.move_cursor(1,10-len(text)//2)
        lcd.print(text)
        text = "Press any button"
        lcd.move_cursor(2,10-len(text)//2)
        lcd.print(text)
        while True:
            if GPIO.input(ENTER_BUTTON) == GPIO.LOW:
                return
            elif GPIO.input(CANCEL_BUTTON) == GPIO.LOW:
                return
            elif GPIO.input(UP_BUTTON) == GPIO.LOW:
                return
            elif GPIO.input(DOWN_BUTTON) == GPIO.LOW:
                return
            elif GPIO.input(VIEW_BUTTON) == GPIO.LOW:
                return
        # if response is not None:
        #     print("Response text:", response.text)
    # finally:
    #     input("Press Enter to continue...")
    
def manual():
    text = ["Thank You", "Your Order", "is being Processed", "Order cancelled"]
    while True:
        menupick, menu, order_counts = select_menu()
        price = 0
        for i in menupick:
            print(f'{menu[i-1]["fields"]["name"]["stringValue"]} - Rp.{menu[i-1]["fields"]["price"]["integerValue"]}')
            price += int(menu[i-1]["fields"]["price"]["integerValue"])
            print(f"Total: {price}")
            print("You're food is being cooked, wait and enjoy!")
            # selected_menu = [menu[x-1]["name"] for x in menupick]
        action = display_final_order(order_counts, price)
        if action == "proceed":
            clear_screen()
            lcd.move_cursor(1, 10-len(text[0])//2)
            lcd.print(text[0])
            time.sleep(1)

            clear_screen()
            lcd.move_cursor(1, 10-len(text[1])//2)
            lcd.print(text[1])
            lcd.move_cursor(2, 10-len(text[2])//2)
            lcd.print(text[2])
            time.sleep(2)
            break
        elif action == "cancel":
            clear_screen()
            lcd.move_cursor(1, 10-len(text[3])//2)
            lcd.print(text[3])
            time.sleep(1)
            break
        elif action == "edit":
            continue 
    selected_menu = [{"mapValue":{"fields":{"name":{"stringValue": menu[x-1]["fields"]["name"]["stringValue"]}, "price":{"integerValue": menu[x-1]["fields"]["price"]["integerValue"]}}}} for x in menupick]
    print(selected_menu)
    fb.log_menu(idToken, email, selected_menu, 0)
    
def main():
    text = ["Welcome", "Have You Registered?"]
    while True:
        # os.system('cls' if os.name == 'nt' else 'clear')
        lcd.move_cursor(0, 10-len(text[0])//2)
        lcd.print(text[0])
        lcd.print_line("A. Manually",1)
        lcd.print_line("B. Registered Favorite",2)
        while True:
            if GPIO.input(ENTER_BUTTON) == GPIO.LOW:
                manual()
                time.sleep(0.2)
                break
            elif GPIO.input(CANCEL_BUTTON) == GPIO.LOW:
                time.sleep(0.2)
                lcd.print_line(text[1],0)
                lcd.print_line("A. Yes",1)
                lcd.print_line("B. No", 2)
                # choice = input(">>> ")
                while True:
                    if GPIO.input(ENTER_BUTTON) == GPIO.LOW:
                        order()
                        time.sleep(0.2)
                        break
                    elif GPIO.input(CANCEL_BUTTON) == GPIO.LOW:
                        register()
                        time.sleep(0.2)
                        break
                break
            # elif choice == 'q':
            #     print("-------------------------------\nProgram Terminated.")
            #     break
            # else:
            #     print("Input Invalid!")


if __name__=="__main__":
   main()
        


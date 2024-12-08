import requests
import json
import ast
import cv2
import base64
import fb_utils2 as fb
import os
import time
import numpy as np
import dlib

# config = {
#   "apiKey": "AIzaSyAy-FlE4rL-V2BwJ8oZEVhqiMY3qfqcQsA",
#   "authDomain": "firestore-despro.firebaseapp.com",
#   "databaseURL": "https://firestore-despro-default-rtdb.firebaseio.com",
#   "projectId": "firestore-despro",
#   "storageBucket": "firestore-despro.appspot.com",
#   "messagingSenderId": "290267621401",
#   "appId": "1:290267621401:web:9bad4a9b502013fd96a288",
#   "measurementId": "G-DFY4Z6HJJG",
#   "firestore_url": "https://firestore.googleapis.com"
# }

# auth = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={config["apiKey"]}'
# auth_headers = {"Content-Type": "application/json"}


# email = "admin@gmail.com"
# password = "admin12345"

email = "alexandermaxim8@gmail.com"
# password = "alex12345"
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

# token = fb.init_firebase(email, password)
# idToken = token["idToken"]
# refreshToken = token["refreshToken"]
# print("idToken:\n", idToken)

# firestore_header = {
#     "Authorization": f"Bearer {idToken}",
#     "Content-Type": "application/json"
# }


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
    video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
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

def select_menu():
    menu = fb.get_menu(email)

    # menu = fb.get_menu(idToken, email)
    for i, menu_pilihan in enumerate(menu):
        print(f'{i+1}. {menu_pilihan["fields"]["name"]["stringValue"]} - Rp.{menu_pilihan["fields"]["price"]["integerValue"]}')
    
    while True:
        try:
            print("Pick your favorites!\neg: 3 2 1")
            menupick = input(">> ")
            menupick = list(map(int, menupick.split(' ')))
            # Check if all selections are valid
            # selected_menu = [menu[x-1] for x in menupick]  # This will raise IndexError if an invalid index is chosen
            break  
        except IndexError:
            print("Invalid menu selection. Please enter valid menu numbers.")
        except ValueError:
            print("Invalid input. Please enter numbers only, separated by commas.")

    print(menupick)
    print(menu)
    return menupick, menu

def order():
    response = None
    try:
        img = pengambilan_gambar()
        # img = cv2.imread("orang3.jpg", cv2.COLOR_BGR2RGB)
        retval, buffer = cv2.imencode('.jpg', img)
        image_bytes = buffer.tobytes()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        headers = {'Content-Type': 'application/json'}
        face = {"face": image_base64, "user": email}
        response = requests.post(f"{url}/predict", data=json.dumps(face), headers=headers) 
        print("Rasberry Pi")
        print("berhasil request prediction")
        price = 0
        total_price = 0
        # Access the menu data
        if response.json() == {"error": "No match found"}:
            print("No match found. Please register first.")
            return
        menu_data = response.json()["menu"]

        print("menu_data:", menu_data)
        # print("response:", response.json())
        # print("\nmenu_data :", menu_data)

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

        print("Proceed?(y/n)\nPress e to edit your personalized menu")
        proceed = input(">>> ")
        if proceed == "y":
            print(f"Total: {total_price}")
            print("Your order is being processed, wait and enjoy!")
            selected_menu = [{"mapValue":{"fields":{"name":{"stringValue": menu_name}, "price":{"integerValue": menu_price}}}} for menu_name, menu_price in zip(menu_data["name"], menu_data["price"])]
            fb.log_menu(email, selected_menu, response.json()["match_id"])
        elif proceed == "n":
            print("Order Canceled.")
        else:
            menupick, menu = select_menu()
            selected_menu = [menu[x-1] for x in menupick]
            fb.add_user(response.json()["match_id"], selected_menu, email)
            
            print("Favorite menu updated, proceed order?(y/n)")
            proceed = input(">>> ")
            if proceed == "y":
                total_price = sum(int(menu[x-1]["fields"]["price"]["integerValue"]) for x in menupick)
                print(f"Total: Rp.{total_price}")
                print("Your food is being cooked, please wait and enjoy!")

                selected_menu = [{"mapValue":{"fields":{"name":{"stringValue": menu[x-1]["fields"]["name"]["stringValue"]}, "price":{"integerValue": menu[x-1]["fields"]["price"]["integerValue"]}}}} for x in menupick]
                fb.log_menu(email, selected_menu, response.json()["match_id"])
            else:
                print("Order Canceled.")
            
        
    except requests.exceptions.RequestException as e:
        print("Error during order processing:", e)
        if response:
            print("Response text:", response.text)
    finally:
        input("Press Enter to continue...")


def register():
    response = None
    try:
        menupick, menu = select_menu()
        selected_menu = [menu[x-1] for x in menupick]
        
        print("Get ready to take a picture.")
        img = pengambilan_gambar()
        # img = cv2.imread("orang2.jpg", cv2.COLOR_BGR2RGB)
        retval, buffer = cv2.imencode('.jpg', img)
        image_bytes = buffer.tobytes()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        headers = {'Content-Type': 'application/json'}


        face = {"menu": selected_menu, "face": image_base64, "user": email}
        response = requests.post(f"{url}/train", data=json.dumps(face), headers=headers) 
        response.raise_for_status()
        print("Registration response:", response.text)
        if "similar face" in response.json().get("status",""):
            print("sudah diregister, balik ke menu utama")
            return
        elif "error" in response.json():
            print(f'An error occured: {response.json()["error"]}')
        else:
            total_price = sum(int(menu[x-1]["fields"]["price"]["integerValue"]) for x in menupick)
            print(f"Total: Rp.{total_price}")
            print("Your food is being cooked, please wait and enjoy!")
            
            # selected_menu = [menu["name"] for menu in selected_menu]
            selected_menu = [{"mapValue":{"fields":{"name":{"stringValue": menu[x-1]["fields"]["name"]["stringValue"]}, "price":{"integerValue": menu[x-1]["fields"]["price"]["integerValue"]}}}} for x in menupick]
            fb.log_menu(email, selected_menu, response.json()["new_id"])

    except requests.exceptions.ConnectionError as e:    
        print("Error during order processing:", e)
        # if response is not None:
        #     print("Response text:", response.text)
    finally:
        input("Press Enter to continue...")


def manual():
    menupick, menu = select_menu()
    price = 0
    for i in menupick:
        print(f'{menu[i-1]["fields"]["name"]["stringValue"]} - Rp.{menu[i-1]["fields"]["price"]["integerValue"]}')
        price += int(menu[i-1]["fields"]["price"]["integerValue"])
        print(f"Total: {price}")
        print("You're food is being cooked, wait and enjoy!")
        # selected_menu = [menu[x-1]["name"] for x in menupick]
    selected_menu = [{"mapValue":{"fields":{"name":{"stringValue": menu[x-1]["fields"]["name"]["stringValue"]}, "price":{"integerValue": menu[x-1]["fields"]["price"]["integerValue"]}}}} for x in menupick]
    print(selected_menu)
    fb.log_menu(email, selected_menu, 0)
 
def main():
    while True:
        # os.system('cls' if os.name == 'nt' else 'clear')
        print("Welcome, how do you want to make the order?")
        print("1. Manually")
        print("2. Registered Favorite")
        choice = input(">>> ")
        if choice == '1':
            manual()
        elif choice == '2':
            print("Have been registered?")
            print("1. Yes, pick my favorite")
            print("2. Register new face")
            choice = input(">>> ")
            if choice == '1':
                order()
            elif choice == '2':
                register()
        elif choice == 'q':
            print("-------------------------------\nProgram Terminated.")
            break
        else:
            print("Input Invalid!")


if __name__=="__main__":
   main()
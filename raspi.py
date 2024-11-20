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


email = "admin@gmail.com"
password = "admin12345"
# email = "alexandermaxim8@gmail.com"
# password = "alex12345"

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
idToken, refreshToken = fb.init_firebase(email, password)
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


# def pengambilan_gambar():

#     a = time.time()
#     video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
#     video.set(cv2.CAP_PROP_FRAME_WIDTH, 360)
#     video.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
#     video.set(cv2.CAP_PROP_FPS, 20)
#     video.set(cv2.CAP_PROP_BUFFERSIZE, 3)
#     video.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

#     print("Waktu membuka kamera:", time.time() - a)
#     print("WIDTH, HEIGHT, FPS:", video.get(cv2.CAP_PROP_FRAME_WIDTH),
#           video.get(cv2.CAP_PROP_FRAME_HEIGHT), video.get(cv2.CAP_PROP_FPS))

#     EAR_THRESHOLD = 0.21
#     blink_counter =  0
#     liveness = sudah_pencet = False
#     font = cv2.FONT_HERSHEY_SIMPLEX

#     while True:
#         ret, frame = video.read()
#         if not ret:
#             break

#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = detector(gray)


#         if sudah_pencet:
#             cv2.putText(frame, 'Silahkan kedip', (50, 100), font,
#                         0.7, (0, 0, 255), 2)
#             for face in faces:
#                 shape = predictor(gray, face)
#                 coords = np.array([[p.x, p.y] for p in shape.parts()])
#                 left_eye, right_eye = coords[36:42], coords[42:48]
#                 ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0

#                 if ear < EAR_THRESHOLD:
#                     blink_counter += 1
#                 if blink_counter > 0 and ear> 0.33:
#                     print("Blink detected!")
#                     cv2.imwrite("captured_frame.jpg", frame)
#                     liveness = True
#                     break


#         cv2.putText(frame, f'Kedipan: {blink_counter}', (10, 30),
#                     font, 0.7, (0, 0, 255), 2)
#         cv2.imshow("Capturing", frame)
        
#         key = cv2.waitKey(1) & 0xFF
#         if key == ord('c'):
#             sudah_pencet = True

#         elif key == ord('q') or liveness:
#             break

#     video.release()
#     cv2.destroyAllWindows()
#     return frame

def pengambilan_gambar():

    a = time.time()
    video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    video.set(cv2.CAP_PROP_FRAME_WIDTH, 360)
    video.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    video.set(cv2.CAP_PROP_FPS, 20)
    video.set(cv2.CAP_PROP_BUFFERSIZE, 3)
    video.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    print("Waktu membuka kamera:", time.time() - a)
    print("WIDTH, HEIGHT, FPS:", video.get(cv2.CAP_PROP_FRAME_WIDTH),
          video.get(cv2.CAP_PROP_FRAME_HEIGHT), video.get(cv2.CAP_PROP_FPS))

    EAR_THRESHOLD = 0.21
    blink_counter = 0
    liveness = sudah_pencet = False
    font = cv2.FONT_HERSHEY_SIMPLEX

    while True:
        ret, frame = video.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        if len(faces) > 0:
            # Menghitung area dari setiap wajah dan memilih yang terbesar
            face_areas = [(face.right() - face.left()) * (face.bottom() - face.top()) for face in faces]
            max_area_index = face_areas.index(max(face_areas))
            face = faces[max_area_index]

            # Menggambar bounding box di sekitar wajah terbesar
            x1 = face.left()
            y1 = face.top()
            x2 = face.right()
            y2 = face.bottom()
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            if sudah_pencet:
                cv2.putText(frame, 'Silahkan kedip', (50, 100), font,
                            0.7, (0, 0, 255), 2)

                shape = predictor(gray, face)
                coords = np.array([[p.x, p.y] for p in shape.parts()])
                left_eye, right_eye = coords[36:42], coords[42:48]
                ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0

                if ear < EAR_THRESHOLD:
                    blink_counter += 1
                if blink_counter > 0 and ear > 0.33:
                    print("Blink detected!")
                    cv2.imwrite("captured_frame.jpg", frame)
                    liveness = True
                    break
            else:
                cv2.putText(frame, 'Tekan huruf "c"', (50, 100), font,
                            0.7, (0, 0, 255), 2)

        cv2.putText(frame, f'Kedipan: {blink_counter}', (10, 30),
                    font, 0.7, (0, 0, 255), 2)
        cv2.imshow("Capturing", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            sudah_pencet = True

        elif key == ord('q') or liveness:
            break

    video.release()
    cv2.destroyAllWindows()
    return frame



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
        response = requests.post("http://127.0.0.1:8000/predict", data=json.dumps(face), headers=headers) 
        #response = requests.post("https://98a1-147-135-15-16.ngrok-free.app/predict", data=json.dumps(face), headers=headers) 
        print("berhasil request")
        price = 0
        total_price = 0
        # Access the menu data
        menu_data = response.json()["menu"]
        print("response:", response.json())
        print("\nmenu_data :", menu_data)

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

        proceed = input("Proceed?(y/n)")
        if proceed == "y":
            print(f"Total: {total_price}")
            print("Your order is being processed, wait and enjoy!")
            fb.log_menu(idToken, email, menu_data["path"])
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
        # databaseId = "(default)"
        # firestore_url = "https://firestore.googleapis.com"
        # parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/admin@gmail.com'
        # collectionId = "menu"
        # response = requests.get(f"{firestore_url}/v1beta1/{parents}/{collectionId}", headers=firestore_header)
        # json_response = response.json()
        # menu = json_response["documents"]
        menu = fb.get_menu(idToken, email)

        # menu = fb.get_menu(idToken, email)
        for i, menu_pilihan in enumerate(menu):
            print(f'{i+1}. {menu_pilihan["fields"]["name"]["stringValue"]} - Rp.{menu_pilihan["fields"]["price"]["integerValue"]}')

        # print("Pick your favorites!\neg: 3 2 1")
        # menupick = input(">> ")

        while True:
            try:
                print("Pick your favorites!\neg: 3 2 1")
                menupick = input(">> ")
                menupick = list(map(int, menupick.split(' ')))
                # Check if all selections are valid
                selected_menu = [menu[x-1] for x in menupick]  # This will raise IndexError if an invalid index is chosen
                break  
            except IndexError:
                print("Invalid menu selection. Please enter valid menu numbers.")
            except ValueError:
                print("Invalid input. Please enter numbers only, separated by commas.")
        
        
        print("Get ready to take a picture.")
        img = pengambilan_gambar()
        # img = cv2.imread("orang2.jpg", cv2.COLOR_BGR2RGB)
        retval, buffer = cv2.imencode('.jpg', img)
        image_bytes = buffer.tobytes()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        headers = {'Content-Type': 'application/json'}


        face = {"menu": selected_menu, "face": image_base64, "user": email, "token":idToken}
        response = requests.post("http://127.0.0.1:8000/train", data=json.dumps(face), headers=headers) 
       # response = requests.post("https://98a1-147-135-15-16.ngrok-free.app/train", data=json.dumps(face), headers=headers) 
        response.raise_for_status()
        print("Registration response:", response.text)

        total_price = sum(int(menu[x-1]["fields"]["price"]["integerValue"]) for x in menupick)
        print(f"Total: Rp.{total_price}")
        print("Your food is being cooked, please wait and enjoy!")

        selected_menu = [menu["name"] for menu in selected_menu]
        fb.log_menu(idToken, email, selected_menu)

    except requests.exceptions.ConnectionError as e:    
        print("Error during order processing:", e)
        # if response is not None:
        #     print("Response text:", response.text)
    finally:
        input("Press Enter to continue...")


def manual():
    # databaseId = "(default)"
    # firestore_url = "https://firestore.googleapis.com"
    # parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/admin@gmail.com'
    # collectionId = "menu"
    # response = requests.get(f"{firestore_url}/v1beta1/{parents}/{collectionId}", headers=firestore_header)
    # json_response = response.json()
    # menu = json_response["documents"]

    menu = fb.get_menu(idToken, email)
    for i, menu_pilihan in enumerate(menu):
        print(f'{i+1}. {menu_pilihan["fields"]["name"]["stringValue"]} - Rp.{menu_pilihan["fields"]["price"]["integerValue"]}')

    # print("Pick your favorites!\neg: 3 2 1")
    # menupick = input(">> ")

    while True:
        try:
            print("Pick your menu!\neg: 3 2 1")
            menupick = input(">> ")
            menupick = list(map(int, menupick.split(' ')))
            # Check if all selections are valid
            # selected_menu = [menu[x-1] for x in menupick]  # This will raise IndexError if an invalid index is chosen
            price = 0
            for i in menupick:
                print(f'{menu[i-1]["fields"]["name"]["stringValue"]} - Rp.{menu[i-1]["fields"]["price"]["integerValue"]}')
                price += int(menu[i-1]["fields"]["price"]["integerValue"])
                print(f"Total: {price}")
                print("You're food is being cooked, wait and enjoy!")
                selected_menu = [menu[x-1]["name"] for x in menupick]
                fb.log_menu(idToken, email, selected_menu)
            break  
        except IndexError:
            print("Invalid menu selection. Please enter valid menu numbers.")
        except ValueError:
            print("Invalid input. Please enter numbers only, separated by commas.")
 
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
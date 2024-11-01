import requests
import json
import ast
import cv2
import base64
import fb_utils as fb

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

auth = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={config["apiKey"]}"
auth_headers = {"Content-Type": "application/json"}


email = "admin@gmail.com"
password = "admin12345"
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

firestore_header = {
    "Authorization": f"Bearer {idToken}",
    "Content-Type": "application/json"
}

while True:
  acc_exist = input("Do you already have a personalized account?(y/n)")
  if acc_exist == "y":
    video = cv2.VideoCapture(0) 
    # 2. Variable
    # 3. While loop
    while True:
      # 4.Create a frame object
      check, frame = video.read()
      # Converting to grayscale
      #gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
      # 5.show the frame!
      cv2.imshow("Capturing",frame)
      # 6.for playing 
      key = cv2.waitKey(1)
      if key == ord('q'):
          break
    video.release()
    cv2.destroyAllWindows() 
    img = frame
    # img = cv2.imread("orang3.jpg", cv2.COLOR_BGR2RGB)
    retval, buffer = cv2.imencode('.jpg', img)
    image_bytes = buffer.tobytes()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    headers = {'Content-Type': 'application/json'}
    face = {"face": image_base64, "user": email}
    response = requests.post("http://127.0.0.1:8000/predict", data=json.dumps(face), headers=headers) 
    print(response)
    print(response.json())

    price = 0
    for i, menu_pilihan in enumerate(response.json()["menu"]):
      print(f"{i+1}. {menu_pilihan["fields"]["name"]["stringValue"]} - Rp.{menu_pilihan["fields"]["price"]["integerValue"]}")
      price += int(menu_pilihan[i-1]["fields"]["price"]["integerValue"])

    proceed = input("Proceed?(y/n)")
    if proceed == "y":
      print(f"Total: {price}")
      print("You're food is being cooked, wait and enjoy!")
      continue
    
  print("How you doin? Please grab some food!")

  databaseId = "(default)"
  firestore_url = "https://firestore.googleapis.com"
  parents = f"projects/{config["projectId"]}/databases/{databaseId}/documents/users/admin@gmail.com"
  collectionId = "menu"
  response = requests.get(f"{firestore_url}/v1beta1/{parents}/{collectionId}", headers=firestore_header)
  json_response = response.json()
  menu = json_response["documents"]
  # menu = fb.get_menu(idToken, email)
  for i, menu_pilihan in enumerate(menu):
    print(f"{i+1}. {menu_pilihan["fields"]["name"]["stringValue"]} - Rp.{menu_pilihan["fields"]["price"]["integerValue"]}")

  menupick = input("Pick yours:")
  if not menupick.startswith("["):
    menupick = "[" + menupick + "]"
  menupick = list(ast.literal_eval(menupick))

  register_new = input("Do you want to add a new personalization account?")

  if bool(register_new):
    video = cv2.VideoCapture(0) 
    # 2. Variable
    # 3. While loop
    while True:
      # 4.Create a frame object
      check, frame = video.read()
      # Converting to grayscale
      #gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
      # 5.show the frame!
      cv2.imshow("Capturing",frame)
      # 6.for playing 
      key = cv2.waitKey(1)
      if key == ord('q'):
          break
    video.release()
    cv2.destroyAllWindows() 
    img = frame
    # img = cv2.imread("orang2.jpg", cv2.COLOR_BGR2RGB)
    retval, buffer = cv2.imencode('.jpg', img)
    image_bytes = buffer.tobytes()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    headers = {'Content-Type': 'application/json'}
    # name = input("Enter your name: ")
    print(menupick)
    print(menu)
    menu = [menu[x-1] for x in menupick]
    print(menu)
    face = {"menu": menu, "face": image_base64, "user": email, "token":idToken}
    response = requests.post("http://127.0.0.1:8000/train", data=json.dumps(face), headers=headers) 
    print(response.text)

  price = 0
  for i in menupick:
    print(f"{menu[i-1]["fields"]["name"]["stringValue"]} - Rp.{menu[i-1]["fields"]["price"]["integerValue"]}")
    price += int(menu[i-1]["fields"]["price"]["integerValue"])
  print(f"Total: {price}")
  print("You're food is being cooked, wait and enjoy!")
  menu = [menu[x-1] for x in menupick]
  fb.log_menu(idToken, email, menu)

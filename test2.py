import requests 
import cv2
import base64
import json

img = cv2.imread("orang2.jpg", cv2.COLOR_BGR2RGB)
retval, buffer = cv2.imencode('.jpg', img)
image_bytes = buffer.tobytes()
image_base64 = base64.b64encode(image_bytes).decode('utf-8')
headers = {'Content-Type': 'application/json'}
name = input("Enter your name: ")
face = {"name": name, "face": image_base64}
response = requests.post("http://127.0.0.1:8000/train", data=json.dumps(face), headers=headers) 
print(response)
# print(response.text)
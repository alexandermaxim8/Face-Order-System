import requests
import cv2
import json
import base64

img = cv2.imread("orang3.jpg", cv2.COLOR_BGR2RGB)
retval, buffer = cv2.imencode('.jpg', img)
image_bytes = buffer.tobytes()
image_base64 = base64.b64encode(image_bytes).decode('utf-8')
headers = {'Content-Type': 'application/json'}
face = {"face": image_base64}
response = requests.post("https://d583-202-169-43-38.ngrok-free.app/predict", data=json.dumps(face), headers=headers) 
print(response)
print(response.text)
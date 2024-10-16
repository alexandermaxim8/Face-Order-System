import requests 
import cv2

img = cv2.imread("alex2.jpg", cv2.COLOR_BGR2RGB)
retval, buffer = cv2.imencode('.jpg', img)
image_bytes = buffer.tobytes()
headers = {'Content-Type': 'application/octet-stream'}
response = requests.post("http://127.0.0.1:8000/train", data=image_bytes, headers=headers) 
print(response)
print(response.text)
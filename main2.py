from fastapi import FastAPI, UploadFile, Body
from PIL import Image
import os
import io
import cv2
import face_recognition as FR
import pickle
import numpy as np
from pydantic import BaseModel
from typing import List
import uvicorn
from typing import Optional
import base64

id = []
known_face = []

app = FastAPI()

class Item(BaseModel):
    name: Optional[str] = None
    face: str

@app.get("/")
async def root():
    return {"Hello": "Mundo"}

@app.post("/train")
async def train(item: Item):  # Use Body to indicate raw byte data
    image_data = item.face
    name = item.name
    image_bytes = base64.b64decode(image_data)
    try:
        # Debugging print to check if data is received
        print(f"Received {len(image_bytes)} bytes")

        # Convert bytes to image using PIL
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img = np.array(img)  # Convert to NumPy array
            print(f"Image converted to NumPy array with shape: {img.shape}")
        except Exception as e:
            print(f"Error in converting image: {str(e)}")
            return {"error": f"Error in converting image: {str(e)}"}

        # Get face encodings from the image
        try:
            face_encodings = FR.face_encodings(face_image=img, num_jitters=50, model='large')
            if len(face_encodings) == 0:
                return {"error": "No face detected in the image"}
            new_face = face_encodings[0]
        except Exception as e:
            print(f"Error in face encoding: {str(e)}")
            return {"error": f"Error in face encoding: {str(e)}"}

        # Load existing encodings
        if os.path.exists('train.pkl'):
            with open('train.pkl', 'rb') as f:
                data = pickle.load(f)
                id = data["id"]
                known_face = data["known_face"]
        else:
            id = []
            known_face = []

        # Save the new face encoding
        new_id = name
        known_face.append(new_face)
        print(len(known_face))
        id.append(new_id)
        data = {
            "id": id,
            "known_face": known_face
        }

        with open('train.pkl', 'wb') as f:
            pickle.dump(data, f)

        return {"status": "Training completed", "new_id": new_id}

    except Exception as e:
        print(f"General error: {str(e)}")
        return {"error": str(e)}
    
@app.post("/predict")
async def predict(item: Item):
    image_data = item.face
    image_bytes = base64.b64decode(image_data)
    img = Image.open(io.BytesIO(image_bytes))
    img = np.array(img)
    test_faces = FR.face_encodings(face_image = img, num_jitters=50, model='large')[0]

    with open('train.pkl', 'rb') as f:
        data = pickle.load(f)
        id = data["id"]
        known_face = data["known_face"]
    try:
        matches=FR.compare_faces(known_face, test_faces)
    except Exception as e:
        print(f"Compare error: {str(e)}")
        return {"error": str(e)}


    if True in matches:
        matched_idx = matches.index(True)
        return {"match_id": id[matched_idx]}
    else:
        return {"error": "No match found"}
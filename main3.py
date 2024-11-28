from fastapi import FastAPI, UploadFile, Body
from PIL import Image
import os
import io
import cv2
import face_recognition as FR
import pickle
import numpy as np
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import base64
import fb_utils as fb

# token = fb.init_firebase("server@gmail.com", "server12345")

id = []
known_face = []

app = FastAPI()

# class ReferenceValue(BaseModel):
#     referenceValue: str

# class ArrayValue(BaseModel):
#     values: List[ReferenceValue]

# class Fields(BaseModel):
#     id: Optional[int]
#     menu: ArrayValue

# class Fields(BaseModel):
#     name: Optional[int]
#     price: ArrayValue

# class FirestoreDocument(BaseModel):
#     name: str
#     fields: Fields
#     createTime: datetime
#     updateTime: datetime

class PriceField(BaseModel):
    integerValue: str

    def to_dict(self):
        return {
            "integerValue": self.integerValue
        }

class NameField(BaseModel):
    stringValue: str

    def to_dict(self):
        return {
            "stringValue": self.stringValue
        }

class Fields(BaseModel):
    price: PriceField
    name: NameField

    def to_dict(self):
        return {
            "price": self.price.to_dict(),
            "name": self.name.to_dict()
        }

class FirestoreDocument(BaseModel):
    name: str
    fields: Fields
    createTime: str
    updateTime: str

    def to_dict(self):
        return {
            "name": self.name,
            "fields": self.fields.to_dict(),
            "createTime": self.createTime,
            "updateTime": self.updateTime
        }

class Item(BaseModel):
    # name: Optional[str] = None
    menu: Optional[List[FirestoreDocument]] = None
    face: str
    user: str
    token: str
 

def face_recog(img, user):
    face_locations = FR.face_locations(img, model='hog')
    test_faces = FR.face_encodings(face_image = img, known_face_locations=face_locations,
                                     num_jitters=50, model='large')
    print(f"test_faces: {len(test_faces)}")
    if len(test_faces) >0:  # Jika ada wajah terdeteksi
        test_face = test_faces[0]
    else:
        print("No face detected in the image")
 
    with open(f'{user}.pkl', 'rb') as f:
        print("user: ", user)
        data = pickle.load(f)
        id = data["id"]
        known_faces = data["known_face"]
    try:
       # matches=FR.compare_faces(known_face, face_encoding, tolerance=0.3)
       # print("matches: ", matches)
       face_distances= FR.face_distance(known_faces, test_face)
       best_match_index = np.argmin(face_distances)
       print(f"best_match_index: {best_match_index}")
    except Exception as e:
        print(f"Compare error: {str(e)}")
        return {"error": str(e)}
    
    if face_distances[best_match_index] < 0.35: # jarak ecludian 
        print(f"id: {id}")
        id = id[best_match_index]
        id=int(id)
        print(f"id: {id}, distance: {face_distances[best_match_index]:.2f}")
        return {"found": True, "id": id}
    else:
        print(f"id: unknown, distance: {face_distances[best_match_index]:.2f}")
        return {"found": False}


@app.get("/")
async def root():
    return {"Hello": "Mundo"}

@app.post("/train")
async def train(item: Item):  # Use Body to indicate raw byte data
    print("train function")
    image_data = item.face
    # name = item.name
    menu = [document.to_dict() for document in item.menu]
    print(menu)
    user = item.user
    token = item.token
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
        
        if face_recog(img, user)["found"]:
            return {"status": "Training terminated, similar face data had been registered!"}

        # Get face encodings from the image
        try:
            face_locations = FR.face_locations(img, model='hog')
            face_encodings = FR.face_encodings(face_image=img,  known_face_locations=face_locations,
                                               num_jitters=50, model='large')
            if len(face_encodings) == 0:
                return {"error": "No face detected in the image"}
            if len(face_encodings) > 0:
                new_face = face_encodings[0]
        except Exception as e:
            print(f"Error in face encoding: {str(e)}")
            return {"error": f"Error in face encoding: {str(e)}"}

        # Load existing encodings
        if os.path.exists(f'{user}.pkl'):
            with open(f'{user}.pkl', 'rb') as f:
                data = pickle.load(f)
                id = data["id"]
                known_face = data["known_face"]
        else:
            id = []
            known_face = []

        # Save the new face encoding
        print("save the new face encoding")
        new_id = fb.generate_id(token, user)
        known_face.append(new_face)
        # print(len(known_face))
        id.append(new_id)
        print("training id: ", id)
        
        data = {
            "id": id,
            "known_face": known_face
        }

        with open(f'{user}.pkl', 'wb') as f:
            pickle.dump(data, f)

        fb.add_user(token, new_id, menu, user)
        print("Success")

        return {"status": "Training completed", "new_id": new_id, "menu": menu}

    except Exception as e:
        print(f"General error: {str(e)}")
        return {"error": str(e)}
    
@app.post("/predict")
async def predict(item: Item):
    print("predict function")
    user = item.user
    image_data = item.face
    token = item.token
    image_bytes = base64.b64decode(image_data)
    img = Image.open(io.BytesIO(image_bytes))
    img = np.array(img)
    # print("token: ", token)
    # print("user: ", user)
    # print("id: ", id)

    found = face_recog(img, user)
    if found["found"]:
        print("found: ", found)
        id = found["id"]
        menu = fb.get_menu(token, user, id)
        print(menu)
        return {"match_id": id, "menu": menu}

    else:
        return {"error": "No match found"}
    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

    # if True in matches:
    #     id = id[matches.index(True)]
    #     menu = fb.get_menu(token["idToken"], user, id=id)
    #     print("menu: ", menu)
    #     return {"match_id": id, "menu": menu}
    # else:
    #     return {"error": "No match found"}
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
 

def face_recog(img, user):
    face_locations = FR.face_locations(img, model='hog')
    test_faces = FR.face_encodings(face_image = img, known_face_locations=face_locations,
                                     num_jitters=50, model='large')
    print(f"test_faces: {len(test_faces)}")
    if len(test_faces) >0:  # Jika ada wajah terdeteksi
        test_face = test_faces[0]
    else:
        print("No face detected in the image")
    
    if os.path.exists(f'{user}.pkl'):
        with open(f'{user}.pkl', 'rb') as f:
            print("user: ", user)
            data = pickle.load(f)
            id = data["id"]
            known_faces = data["known_face"]
    else:
        return {"found": False}
    
    try:
       # matches=FR.compare_faces(known_face, face_encoding, tolerance=0.3)
       # print("matches: ", matches)
       face_distances= FR.face_distance(known_faces, test_face)
       best_match_index = np.argmin(face_distances)
       print(f"best_match_index: {best_match_index}")
    except Exception as e:
        print(f"Compare error: {str(e)}")
        # return {"error": str(e)}
        return {"found": False}
    
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
        new_id = fb.generate_id(user)
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

        fb.add_user(new_id, menu, user)
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

        menu = fb.get_menu(user, id)
        menu_name=np.array(menu["name"])
        menu_ref=np.array(menu["reference"])
        print("prediction function menu: ", menu_name )
        # print("prediction function reference: ", menu_ref)

        menu_all= fb.get_menu(user)
        menu_all_name=[]
        menu_all_ref=[]
        for i, all in enumerate(menu_all):
            menu_all_name.append(all["fields"]["name"]["stringValue"])
            menu_all_ref.append(all["name"])
        print("menu_all_name: ", menu_all_name)
        # print("menu_all reference: ", menu_all_ref)
        menu_all_name=np.array(menu_all_name)
        menu_all_ref=np.array(menu_all_ref)

        index_menu_dihapus= np.where(~np.isin(menu_name, menu_all_name))[0]
        if index_menu_dihapus.size>0:
            print("Maaf makanan anda sudah dihapus")
            print("index_menu_dihapus: ", index_menu_dihapus)
            print("makanan dihapus: ", menu_name[index_menu_dihapus])
            # menu_ref[index_menu_dihapus]
            fb.delete_menu_item_from_customer(user, menu_ref[index_menu_dihapus], id)
    
        print("Berhasil menu delete")
        # menu_name=np.delete(menu_name, index_menu_dihapus)
        # print("menu_name_delete: ", menu_name)
        # if menu_all
        print("menu:", menu)
        menu_final_pelanggan={"name": np.delete(menu["name"], index_menu_dihapus).tolist(), 
                              "price": np.delete(menu["price"], index_menu_dihapus).tolist(),
                                "reference":  np.delete(menu["reference"], index_menu_dihapus).tolist()}
        print("menu_final_pelanggan: ", menu_final_pelanggan)
        return {"match_id": id,"menu": menu_final_pelanggan}

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
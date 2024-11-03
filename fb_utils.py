import requests
import json
import random
import uuid
from datetime import datetime, timezone
import numpy as np

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
firestore_url = "https://firestore.googleapis.com"
databaseId = "(default)"

def init_firebase(email, password):
    auth = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={config["apiKey"]}'
    auth_headers = {"Content-Type": "application/json"}
    data = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(auth, data=json.dumps(data), headers=auth_headers)
    json_response = response.json()
    # print(json_response)
    idToken = json_response["idToken"]
    refreshToken = json_response["refreshToken"]
    return idToken, refreshToken

def generate_id(idToken, user):
    print("generate_id function") 
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }
    parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}'
    collectionId = "pelanggan"
    response = requests.get(f"{firestore_url}/v1/{parents}/{collectionId}", headers=firestore_header)
    json_response = response.json()
    #print(json_response)
    ids = [int(doc["fields"]["id"]["integerValue"]) for doc in json_response["documents"]]
    print("ids sekarang: ", ids)
    r = int(np.max(ids))+1 if ids else 1
    print("r: ", r)
    return r


def add_user(idToken, id, menu, user):
    parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}'
    collectionId = "pelanggan"
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }
 
    data = {
    "fields": {
        "id": {
            "integerValue":f"{id}"
        },
        "menu":{
            "arrayValue":{
                "values":[{"referenceValue": x["name"]} for x in menu]
                }
            }
        }
    }
    response = requests.patch(f"{firestore_url}/v1beta1/{parents}/{collectionId}/{id}", data=json.dumps(data), headers=firestore_header)
    print(response.json())

def get_menu(idToken, user, id=None):
    print("\nget_menu function")
    print("idToken", idToken)
    print("user", user)
    print("id", id)
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }
    if id:
        menu = {"name":[], "price":[]}
        name = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/pelanggan/{id}'
        response = requests.get(f"{firestore_url}/v1beta1/{name}", headers=firestore_header)
        print("response: ", response.json())
        ref = response.json()["fields"]["menu"]["arrayValue"]["values"]
        print("ref", ref)

        # Loop through each item in ref, which should be a list of dictionaries
        for ref_item in ref:
            # Extract the reference path from each item
            reference = ref_item.get("referenceValue")
            if reference:
                response = requests.get(f"{firestore_url}/v1beta1/{reference}", headers=firestore_header)
                document = response.json().get("fields", {})

                # Assuming the response contains 'name' and 'price' fields, append them to menu
                menu["name"].append(document.get("name", {}).get("stringValue", ""))
                menu["price"].append(document.get("price", {}).get("integerValue", 0))

    
        # for ref in ref["referenceValue"]:
        #     response = requests.get(f"{firestore_url}/v1beta1/{ref}", headers=firestore_header)
        #     # menu["name"].append(response.json()["documents"]["fields"]["name"]["stringValue"])
        #     # menu["price"].append(response.json()["documents"]["fields"]["price"]["integerValue"])
        #     menu.append(response.json()["documents"])
    else:
        parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}'
        collectionId = "menu"
        response = requests.get(f"{firestore_url}/v1beta1/{parents}/{collectionId}", headers=firestore_header)
        json_response = response.json()
        menu = json_response["documents"]
    print("menu: ", menu)
    return menu

def log_menu(idToken, user, menu):
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }
    parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}'
    collectionId = "sales"
    data = {
    "fields": {
        "datetime": {
            "timestampValue":f'{datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}'
        },
        "menu":{
            "arrayValue":{
                "values":[{"referenceValue": x["name"]} for x in menu]
                }
            }
        }
    }
    response = requests.post(f"{firestore_url}/v1beta1/{parents}/{collectionId}", data=json.dumps(data), headers=firestore_header)
    print(response.json())

# def edit_menu(id, id_menu, user):
#     menu = []
#     for i in id_menu:
#         obj = user.collection("menu").where("id", "==", i).stream()
#         for doc in obj:
#             menu.append(doc.to_dict())
#     user.collection("pelanggan").document(id).update({"menu": menu})

# def add_menu(menu, price, user):
#     user.collection("menu").add({
#         "name":menu,
#         "price":price
#     })
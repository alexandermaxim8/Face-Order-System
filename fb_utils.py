import requests
import json
import random
import uuid
from datetime import datetime, timezone, timedelta
import numpy as np
from collections import Counter

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
    if response.status_code == 200:
    # print(json_response)
        idToken = json_response["idToken"]
        refreshToken = json_response["refreshToken"]
        return {"idToken": idToken, "refreshToken": refreshToken}
    else:
        error_message = json_response["error"]["message"]
        if error_message == "EMAIL_NOT_FOUND":
            return {"Error": "No user found with this email. Please check your email address."}
        elif error_message == "INVALID_PASSWORD":
            return {"Error": "The password is invalid. Please check your password."}
        elif error_message == "USER_DISABLED":
            return {"Error": "This account has been disabled. Please contact support."}
        else:
            return {"Error": f"Authentication failed with message: {error_message}"}

def generate_id(idToken, user, menu=False):
    #print("generate_id function") 
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }
    if not menu:
        parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}'
        collectionId = "pelanggan"
        response = requests.get(f"{firestore_url}/v1/{parents}/{collectionId}", headers=firestore_header)
        json_response = response.json()
        #print(json_response)
        if not json_response:
            print("Empty JSON response!")
            return 1
        ids = [int(doc["fields"]["id"]["integerValue"]) for doc in json_response["documents"]]
    else:
        parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/'
        query_body = {
            "structuredQuery": {
                "from": [{"collectionId": "menu"}]
            }
        }
        response = requests.post(f"{firestore_url}/v1/{parents}:runQuery", headers=firestore_header, data=json.dumps(query_body))
        json_response = response.json()
        for doc in json_response:
            ids = [int(doc["document"]["name"].split('/')[-1]) for doc in json_response]
        # ids = [int(doc["fields"]["id"]["integerValue"]) for doc in json_response["documents"]]
    #print("ids sekarang: ", ids)
    r = int(np.max(ids))+1
    #print("r: ", r)
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
   # print(response.json())

def get_menu(idToken, user, id=None):
    # print("\nget_menu function")
    # print("idToken", idToken)
    # print("user", user)
    # print("id", id)
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }
    if id:
        menu = {"name":[], "price":[], "path":[]}
        name = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/pelanggan/{id}'
        response = requests.get(f"{firestore_url}/v1beta1/{name}", headers=firestore_header)
        #print("response: ", response.json())
        ref = response.json()["fields"]["menu"]["arrayValue"]["values"]
        #print("ref", ref)

        # Loop through each item in ref, which should be a list of dictionaries
        for ref_item in ref:
            # Extract the reference path from each item
            reference = ref_item.get("referenceValue")
            if reference:
                response = requests.get(f"{firestore_url}/v1beta1/{reference}", headers=firestore_header)
                document = response.json().get("fields", {})
                path = response.json().get("name", {})

                # Assuming the response contains 'name' and 'price' fields, append them to menu
                menu["name"].append(document.get("name", {}).get("stringValue", ""))
                menu["price"].append(document.get("price", {}).get("integerValue", 0))
                menu["path"].append(path)

    
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
    #print("menu: ", menu)
    return menu

def log_menu(idToken, user, menu, id):
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }
    parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}'
    collectionId = "sales"

    utc7_time = datetime.now(timezone(timedelta(hours=7)))
    utc7_time_iso = str(utc7_time.isoformat())
    data = {
    "fields": {
        "datetime": {
            # "timestampValue":f'{datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}'
            "timestampValue":utc7_time_iso
        },
        "menu":{
            "arrayValue":{
                "values": menu
                }
            },
        "id":{
            "integerValue": str(id)
            },
        "done": {
            "booleanValue": "false"
            }
        }
    }
    # response = requests.patch(f"{firestore_url}/v1/{parents}/{collectionId}/{str(datetime.now(timezone(timedelta(hours=7))))}", data=json.dumps(data), headers=firestore_header)
    response = requests.patch(f"{firestore_url}/v1/{parents}/{collectionId}/{utc7_time.strftime("%Y-%m-%d %H:%M:%S")}", data=json.dumps(data), headers=firestore_header)
    #print(response.json())

def convert_utc7(date_time):
    utc_time = datetime.fromisoformat(date_time.replace("Z", "+00:00"))
    utc_plus_7 = utc_time.astimezone(timezone(timedelta(hours=7)))
    return utc_plus_7.strftime("%Y-%m-%d")

def convert_utc(date_time):
    utc7_time = datetime.fromisoformat(date_time)
    utc_time = utc7_time - timedelta(hours=7)
    return utc_time.isoformat() + "Z"

def get_sales(idToken, user, start, end):
    # date = []
    date_list = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end - start).days + 1)]
    json_response = query_log(idToken, user, start, end)
   # print(json_response)
    total = [0 for i in range(len(date_list))]
    if "document" in json_response[0]:
        for doc in json_response:
            doc["document"]["fields"]["datetime"]["timestampValue"] = convert_utc7(doc["document"]["fields"]["datetime"]["timestampValue"])
        # date.append(doc["document"]["fields"]["datetime"]["timestampValue"])

        # date = sorted(list(set(date)))
        for i, date in enumerate(date_list):
            for doc in json_response:
                if doc["document"]["fields"]["datetime"]["timestampValue"] == date:
                    total[i] = total[i] + sum([int(x["mapValue"]["fields"]["price"]["integerValue"]) for x in doc["document"]["fields"]["menu"]["arrayValue"]["values"]])

    #print(date_list)
    #print(total)
    return date_list, total

def get_menuranks(idToken, user, start, end):
    json_response = query_log(idToken, user, start, end)
    menu = ["None"]
    counts = [0]
    if "document" in json_response[0]:
        menus_counts = Counter(x["mapValue"]["fields"]["name"]["stringValue"] 
                        for doc in json_response
                        for x in doc["document"]["fields"]["menu"]["arrayValue"]["values"] )
        menu = [menu for menu, count in menus_counts.items()]  # List of keys
        counts = [count for menu, count in menus_counts.items()]
    # result = [{"name": name, "count": count} for name, count in menus_counts.items()]
    return menu, counts

def query_log(idToken, user, start, end):
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }

    parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/'
    query_body = {
        "structuredQuery": {
            "from": [{"collectionId": "sales"}],
            "where": {
                "compositeFilter": {
                    "op": "AND",
                    "filters": [
                        {
                            "fieldFilter": {
                                "field": {"fieldPath": "datetime"},
                                "op": "GREATER_THAN_OR_EQUAL",
                                "value": {"timestampValue": convert_utc(f"{start}T00:00:00")}
                            }
                        },
                        {
                            "fieldFilter": {
                                "field": {"fieldPath": "datetime"},
                                "op": "LESS_THAN_OR_EQUAL",
                                "value": {"timestampValue": convert_utc(f"{end}T23:59:59")}
                            }
                        }
                    ]
                }
            }
        }
    }

    response = requests.post(f"{firestore_url}/v1/{parents}:runQuery", headers=firestore_header, data=json.dumps(query_body))
    json_response = response.json()

    return json_response

def add_menu(menu_name, menu_price, idToken, user):
    print("Menambahkan menu:", menu_name)
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }
    parent = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/menu'
    document_id = menu_name.replace(" ", "_")  # Membuat ID dokumen unik

    data = {
        "fields": {
            "name": {"stringValue": menu_name},
            "price": {"integerValue": str(int(menu_price))}
        }
    }

    # URL untuk membuat atau memperbarui dokumen dengan ID tertentu
    url = f"{firestore_url}/v1/{parent}/{generate_id(idToken, user, True)}"

    # Mengirim permintaan PATCH untuk menambahkan atau memperbarui dokumen
    response = requests.patch(url, data=json.dumps(data), headers=firestore_header)

    if response.status_code in [200, 201]:
        print("Menu berhasil ditambahkan.")
        return {"success": True}
    else:
        print(f"Error saat menambahkan menu: {response.text}")
        return {"success": False, "error": response.json()}

def update_menu(idToken, user, menu_id, new_name, new_price):
    print(f"Updating menu ID: {menu_id} with name: {new_name}, price: {new_price}")
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }
    
    # Path ke dokumen menu
    document_path = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/menu/{menu_id}'
    
    # Data yang akan diperbarui
    update_data = {
        "fields": {
            "name": {"stringValue": new_name},
            "price": {"integerValue": str(new_price)}
        }
    }
    # Permintaan PATCH untuk memperbarui dokumen
    response = requests.patch(f"{firestore_url}/v1/{document_path}", data=json.dumps(update_data), headers=firestore_header)
    
    # Cek hasil respons
    if response.status_code == 200:
        print(f"Menu ID {menu_id} updated successfully.")
        return {"success": True, "menu_id": menu_id}
    else:
        print(f"Error updating menu ID {menu_id}: {response.text}")
        return {"success": False, "error": response.json()}


def get_recent_order(idToken, user, update=None, limit=10):
    firestore_header = {
        "Authorization": f"Bearer {idToken}",
        "Content-Type": "application/json"
    }

    if not update is None:
        for date_time in update:
            document_path = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/sales/{date_time}'
            data = {
                "fields": {
                    "done": {"booleanValue": True}
                }
            }
            response = requests.patch(f"https://firestore.googleapis.com/v1/{document_path}?updateMask.fieldPaths=done", headers=firestore_header, data=json.dumps(data))
            print(response.json())
            if response.status_code != 200:
                break       

    parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/'
    query_body = {
        "structuredQuery": {
            "from": [{"collectionId": "sales"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "done"},
                    "op": "EQUAL",
                    "value": {"booleanValue": "false"}
                }
            },
            "orderBy": [{
                "field": {"fieldPath": "datetime"},
                "direction": "DESCENDING"
            }],
            "limit": limit
        }
    }

    response = requests.post(f"{firestore_url}/v1/{parents}:runQuery", headers=firestore_header, data=json.dumps(query_body))
    json_response = response.json()
    # print(json_response)

    return json_response
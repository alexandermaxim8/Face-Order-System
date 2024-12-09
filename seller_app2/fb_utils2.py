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

def generate_id(user, menu=False):
    if not menu:
        parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}'
        collectionId = "pelanggan"
        response = requests.get(f"{firestore_url}/v1/{parents}/{collectionId}")
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
        response = requests.post(f"{firestore_url}/v1/{parents}:runQuery", data=json.dumps(query_body))
        json_response = response.json()
        for doc in json_response:
            ids = [int(doc["document"]["name"].split('/')[-1]) for doc in json_response]
        # ids = [int(doc["fields"]["id"]["integerValue"]) for doc in json_response["documents"]]
    #print("ids sekarang: ", ids)
    r = int(np.max(ids))+1
    #print("r: ", r)
    return r

def add_user(id, menu, user):
    parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}'
    collectionId = "pelanggan"

    data = {
    "fields": {
        "id": {
            "integerValue":f"{id}"
        },
        "menu":{
            "arrayValue":{
                "values":[{"mapValue":{"fields":{"name":{"stringValue": x["fields"]["name"]["stringValue"]}, "price":{"integerValue": x["fields"]["price"]["integerValue"]}, "ref":{"referenceValue": x["name"]}}}} for x in menu]
                }
            }
        }
    }
    response = requests.patch(f"{firestore_url}/v1beta1/{parents}/{collectionId}/{id}", data=json.dumps(data))
   # print(response.json())

def get_menu(user, id=None):
    if id:
        menu = {"name":[], "price":[], "reference":[]}

        name = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/pelanggan/{id}'
        response = requests.get(f"{firestore_url}/v1beta1/{name}")
        #print("response: ", response.json())
        menu_items = response.json()["fields"]["menu"]["arrayValue"]["values"]
        

        # Loop through each item in ref, which should be a list of dictionaries
        for item in menu_items:
            fields = item.get('mapValue', {}).get('fields', {})
            
            # Ambil 'name', 'price', dan 'ref'
            name = fields.get('name', {}).get('stringValue', '')
            price = int(fields.get('price', {}).get('integerValue', 0))
            reference = fields.get('ref', {}).get('referenceValue', '')
            
            # Tambahkan ke list
            menu["name"].append(name)
            menu["price"].append(price)
            menu["reference"].append(reference)

    else:
        parents = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}'
        collectionId = "menu"
        response = requests.get(f"{firestore_url}/v1beta1/{parents}/{collectionId}")
        json_response = response.json()
        menu = json_response["documents"]
    return menu


def delete_menu_item_from_customer(idToken, user, menu_ref_list, customer_id):
    # Document path for the customer
    document_path = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/pelanggan/{customer_id}'
    
    # Fetch the customer document
    response = requests.get(f"{firestore_url}/v1/{document_path}")
    if response.status_code != 200:
        print(f"Error fetching customer document: {response.json()}")
        return
    
    customer_doc = response.json()
    # print("customer_doc:", customer_doc)
    
    # Extract the 'menu' field from the customer document
    fields = customer_doc.get('fields', {})
    menu_items = fields.get('menu', {}).get('arrayValue', {}).get('values', [])
    
    # Check if 'menu' field exists
    if not menu_items:
        print("No menu items found for the customer.")
        return
    
    # print("Current menu items:")
    for item in menu_items:
        item_fields = item.get('mapValue', {}).get('fields', {})
        name = item_fields.get('name', {}).get('stringValue', '')
        ref = item_fields.get('ref', {}).get('referenceValue', '')
        price = item_fields.get('price', {}).get('integerValue', '')
        print(f"- Name: {name}, Ref: {ref}, Price: {price}")
    
    # Remove the menu items with refs in menu_ref_list
    new_menu_items = []
    items_removed = False
    for item in menu_items:
        item_fields = item.get('mapValue', {}).get('fields', {})
        ref = item_fields.get('ref', {}).get('referenceValue', '')
        if ref in menu_ref_list:
            items_removed = True
            print(f"Removing menu item with ref: {ref}")
            continue  # Skip this item to remove it from the list
        new_menu_items.append(item)
    
    if not items_removed:
        print(f"No matching menu items found in customer's menu.")
        return
    
    # Prepare the updated menu items
    updated_menu_field = {
        'arrayValue': {
            'values': new_menu_items
        }
    }
    
    # Update the customer document with the modified menu
    update_data = {
        'fields': {
            'menu': updated_menu_field
        }
    }
    
    update_response = requests.patch(
        f"{firestore_url}/v1/{document_path}?updateMask.fieldPaths=menu",
        json=update_data
    )
    
    if update_response.status_code == 200:
        print("Menu items deleted successfully from customer.")
    else:
        print(f"Error updating customer document: {update_response.json()}")

def log_menu(user, menu, id):
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
    response = requests.patch(f'{firestore_url}/v1/{parents}/{collectionId}/{utc7_time.strftime("%Y-%m-%d %H:%M:%S")}', data=json.dumps(data))
    #print(response.json())

def convert_utc7(date_time):
    utc_time = datetime.fromisoformat(date_time.replace("Z", "+00:00"))
    utc_plus_7 = utc_time.astimezone(timezone(timedelta(hours=7)))
    return utc_plus_7.strftime("%Y-%m-%d")

def convert_utc(date_time):
    utc7_time = datetime.fromisoformat(date_time)
    utc_time = utc7_time - timedelta(hours=7)
    return utc_time.isoformat() + "Z"

def get_sales(user, start, end):
    # date = []
    date_list = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end - start).days + 1)]
    print(date_list)
    json_response = query_log(user, start, end)
   # print(json_response)
    total = [0 for i in range(len(date_list))]
    if "document" in json_response[0]:
        for doc in json_response:
            doc["document"]["fields"]["datetime"]["timestampValue"] = convert_utc7(doc["document"]["fields"]["datetime"]["timestampValue"])

        for i, date in enumerate(date_list):
            for doc in json_response:
                if doc["document"]["fields"]["datetime"]["timestampValue"] == date:
                    if doc["document"]["fields"]["done"]["booleanValue"] == True:
                        sum = 0
                        for x in doc["document"]["fields"]["menu"]["arrayValue"]["values"]:
                            if "quantity" in x["mapValue"]["fields"]:
                                sum += int(x["mapValue"]["fields"]["price"]["integerValue"])*int(x["mapValue"]["fields"]["quantity"]["integerValue"])
                            else:
                                sum += int(x["mapValue"]["fields"]["price"]["integerValue"])
                        total[i] += sum
                    else:
                        total[i] += 0

                        # total[i] = total[i] + sum([int(x["mapValue"]["fields"]["price"]["integerValue"]) 
                        #                            for x in doc["document"]["fields"]["menu"]["arrayValue"]["values"]])

    return date_list, total

def get_menuranks(user, start, end):
    json_response = query_log(user, start, end)
    menu = ["None"]
    counts = [0]
    if "document" in json_response[0]:
        menus_counts = Counter()

        # Loop through the json_response
        for doc in json_response:
            # Check if 'done' is True in the document
            if doc["document"]["fields"]["done"]["booleanValue"] == True:
                
                # Loop through the menu values
                for x in doc["document"]["fields"]["menu"]["arrayValue"]["values"]:
                    
                    # Check if 'quantity' exists in the current item
                    if "quantity" in x["mapValue"]["fields"]:
                        # Repeat the name based on the quantity
                        name = x["mapValue"]["fields"]["name"]["stringValue"]
                        qty = int(x["mapValue"]["fields"]["quantity"]["integerValue"])
                        
                        # Add the name repeated qty times
                        for _ in range(qty):
                            menus_counts[name] += 1
                    else:
                        # If 'quantity' doesn't exist, just add the name once
                        name = x["mapValue"]["fields"]["name"]["stringValue"]
                        menus_counts[name] += 1

        # menus_counts = Counter(x["mapValue"]["fields"]["name"]["stringValue"]*int(x["mapValue"]["qty"]["price"]["integerValue"])
        #                        if "qty" in x["mapValue"]["fields"]["qty"]
        #                        else
        #                 for doc in json_response
        #                 if doc["document"]["fields"]["done"]["booleanValue"] == "true"
        #                 for x in doc["document"]["fields"]["menu"]["arrayValue"]["values"] )
        menu = [menu for menu, count in menus_counts.items()]  # List of keys
        counts = [count for menu, count in menus_counts.items()]
    # result = [{"name": name, "count": count} for name, count in menus_counts.items()]
    return menu, counts

def query_log(user, start, end):
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

    response = requests.post(f"{firestore_url}/v1/{parents}:runQuery", data=json.dumps(query_body))
    json_response = response.json()

    return json_response

def add_menu(menu_name, menu_price, user):
    print("Menambahkan menu:", menu_name)
    parent = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/menu'
    document_id = menu_name.replace(" ", "_")  # Membuat ID dokumen unik

    data = {
        "fields": {
            "name": {"stringValue": menu_name},
            "price": {"integerValue": str(int(menu_price))}
        }
    }

    # URL untuk membuat atau memperbarui dokumen dengan ID tertentu
    url = f"{firestore_url}/v1/{parent}/{generate_id(user, True)}"

    # Mengirim permintaan PATCH untuk menambahkan atau memperbarui dokumen
    response = requests.patch(url, data=json.dumps(data))

    if response.status_code in [200, 201]:
        print("Menu berhasil ditambahkan.")
        return {"success": True}
    else:
        print(f"Error saat menambahkan menu: {response.text}")
        return {"success": False, "error": response.json()}

def update_menu(user, menu_id, new_name, new_price):
    print(f"Updating menu ID: {menu_id} with name: {new_name}, price: {new_price}")
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
    response = requests.patch(f"{firestore_url}/v1/{document_path}", data=json.dumps(update_data))
    
    # Cek hasil respons
    if response.status_code == 200:
        print(f"Menu ID {menu_id} updated successfully.")
        return {"success": True, "menu_id": menu_id}
    else:
        print(f"Error updating menu ID {menu_id}: {response.text}")
        return {"success": False, "error": response.json()}


def get_recent_order(user, update=None, limit=10):
    if not update is None:
        for date_time in update:
            document_path = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/sales/{date_time}'
            data = {
                "fields": {
                    "done": {"booleanValue": True}
                }
            }
            response = requests.patch(f"https://firestore.googleapis.com/v1/{document_path}?updateMask.fieldPaths=done", data=json.dumps(data))
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

    response = requests.post(f"{firestore_url}/v1/{parents}:runQuery", data=json.dumps(query_body))
    json_response = response.json()
    # print(json_response)

    return json_response



def delete_menu(user, menu_id):
    document_path = f'projects/{config["projectId"]}/databases/{databaseId}/documents/users/{user}/menu/{menu_id}'
    
    # Mengirim request DELETE ke Firestore
    response = requests.delete(f"{firestore_url}/v1/{document_path}")
    
    if response.status_code == 200:
        print(f"Menu ID {menu_id} berhasil dihapus.")
        return {"success": True}
    else:
        print(f"Gagal menghapus menu ID {menu_id}: {response.text}")
        return {"success": False, "error": response.json()}
    
def get_user(user):
    response = requests.get("https://firestore.googleapis.com/v1beta1/projects/firestore-despro/databases/(default)/documents/users")
    existing_user = [x["name"].split('/')[-1] for x in response.json()["documents"]]
    if user in existing_user:
        return True
    else:
        return False
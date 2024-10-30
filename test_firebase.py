import requests
import json

projectId = "firestore-despro"
databaseId = "(default)"
apikey = "AIzaSyAy-FlE4rL-V2BwJ8oZEVhqiMY3qfqcQsA"
auth = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={apikey}"
data = {"email": "admin@gmail.com", "password": "admin12345", "returnSecureToken": True}
headers = {"Content-Type": "application/json"}

response = requests.post(auth, data=json.dumps(data), headers=headers)

json_response = response.json()
# print(json_response)

idToken = json_response["idToken"]
refreshToken = json_response["refreshToken"]

firestore_header = {
    "Authorization": f"Bearer {idToken}",
    "Content-Type": "application/json"
}

firestore_url = "https://firestore.googleapis.com"
database = f"projects/{projectId}/databases/{databaseId}"
data = {
    "documents": [
        f"{database}/documents/users/admin@gmail.com/menu/1",
        f"{database}/documents/users/admin@gmail.com/menu/2"
    ]
}

response = requests.post(f"{firestore_url}/v1beta1/{database}/documents:batchGet", data=json.dumps(data), headers=firestore_header)
# print(response.json())

parents = f"projects/{projectId}/databases/{databaseId}/documents/users/admin@gmail.com"
collectionId = "menu"
response = requests.get(f"{firestore_url}/v1beta1/{parents}/{collectionId}", headers=firestore_header)
# print(response.json())

parents = f"projects/{projectId}/databases/{databaseId}/documents/users/admin@gmail.com"
collectionId = "pelanggan"
response = requests.get(f"{firestore_url}/v1beta1/{parents}/{collectionId}", headers=firestore_header)
print(response.json())
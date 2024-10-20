import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import random

cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client() # Database reference

def add_user(id, id_menu):
    menu = []
    ids = [doc.id for doc in db.collection('pelanggan').get()]
    while True:
        r = random.randint(1,100)
        if r not in ids:
            break
    for i in id_menu:
        obj = db.collection("menu").where("id", "==", i).stream()
        for doc in obj:
            menu.append(doc.to_dict())
    db.collection("pelanggan").document(r).set(
        {"menu":menu}
    )

def get_menu(id):
    menu = []
    if id:
        doc_ref = db.collection("pelanggan").document(id).get()
        menu = doc_ref.to_dict()
    else:
        for doc in db.collection('menu').get():
            menu.append(doc.to_dict())

    print(menu)
    return menu

def edit_menu(id, id_menu):
    menu = []
    for i in id_menu:
        obj = db.collection("menu").where("id", "==", i).stream()
        for doc in obj:
            menu.append(doc.to_dict())
    db.collection("pelanggan").document(id).update({"menu": menu})

def add_menu(menu, price):
    db.collection("menu").add({
        "name":menu,
        "price":price
    })
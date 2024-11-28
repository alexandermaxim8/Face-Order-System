import streamlit as st
from time import sleep
from navigation import make_sidebar
import fb_utils2 as fb

@st.dialog("Login Error")
def login_error(message):
    st.write(message)

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

auth = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={config["apiKey"]}'
auth_headers = {"Content-Type": "application/json"}

st.empty()
hide_sidebar_style = """
    <style>
    [data-testid="stSidebar"] {
        display: none;  /* Hide the entire sidebar */
    }
    [data-testid="stSidebarNav"] {
        display: none;  /* Hide the sidebar navigation */
    }
    [data-testid="stSidebarToggle"] {
        display: none !important;  /* Hides the toggle button container */
    }
    svg[aria-hidden="true"] { 
        display: none !important;  /* Hides the SVG element (the arrow icon) */
    }
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

# Initialize session state if not already defined
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Call sidebar logic (will remain empty for non-logged-in users)
make_sidebar()

st.title("📱Welcome to Face-Order Seller App")
st.write("Please log in to continue (email `alexandermaxim8@gmail.com`, password `alex12345`).")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

token = fb.init_firebase(email, password)

if st.button("Log in", type="primary"):
    if "idToken" in token:
        st.session_state.logged_in = True  # Set the login state
        st.session_state["idToken"] = token["idToken"]
        st.session_state["email"] = email
        st.success("Logged in successfully!")
        sleep(0.5)
        st.switch_page("pages/page1.py")  # Redirect to a new page
    else:
        login_error(token["Error"])
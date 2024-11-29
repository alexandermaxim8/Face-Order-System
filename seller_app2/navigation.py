import streamlit as st
import time

def make_sidebar():
    with st.sidebar:
        if st.session_state.logged_in:
            st.page_link("pages/page1.py", label="Sales Analytics", icon="📈")
            st.page_link("pages/page2.py", label="Menubase", icon="🍔")
            st.page_link("pages/page3.py", label="Pesanan", icon="📜")

            st.write("")
            st.write("")

            st.title(f'Hello {st.session_state["email"].split("@")[0]}👋')

            if st.button("Log out"):
                logout()
        else:
            st.empty()

def logout():
    st.session_state.logged_in = False
    st.session_state.clear()
    st.info("Logged out successfully!")
    time.sleep(0.5)
    st.switch_page("login.py")
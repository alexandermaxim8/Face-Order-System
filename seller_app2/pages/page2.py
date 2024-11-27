from navigation import make_sidebar
import helper as hp
import streamlit as st

hide_navigation_style = """
    <style>
    [data-testid="stSidebarNav"] > ul:first-child {
        display: none;
    }
    </style>
"""
st.markdown(hide_navigation_style, unsafe_allow_html=True)

make_sidebar()

st.write(
    """
# 🕵️ EVEN MORE SECRET

This is a secret page that only logged-in users can see.

Super duper secret.

Shh....

"""
)
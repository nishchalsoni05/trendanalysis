
import streamlit as st
try:
    print(f"st.page_link available: {'page_link' in dir(st)}")
except:
    print("Error checking st")

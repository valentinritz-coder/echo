import os

import requests
import streamlit as st

PROJECT_NAME = "echo-mvp"
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

st.set_page_config(page_title=PROJECT_NAME)
st.title("Echo MVP (capsule de vie)")
st.write("Squelette Streamlit prêt pour les prochaines itérations.")
st.caption(f"API_BASE_URL: {API_BASE_URL}")

try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    response.raise_for_status()
    st.success(f"API en ligne: {response.json()}")
except requests.RequestException as exc:
    st.warning(f"API indisponible: {exc}")

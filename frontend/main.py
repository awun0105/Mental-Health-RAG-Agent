import requests
import streamlit as st

st.set_page_config(
    page_title="Mental Health AI Platform",
    page_icon="🧠",
    layout="wide",
)

st.title("Mental Health AI Platform")
st.write("Welcome to the Mental Health Sovereign Agentic AI Platform")

st.title("Test Connection")

# Nút bấm để gọi API
if st.button("Check Backend Health"):
    try:
        # Gọi đến URL của Backend
        response = requests.get("http://localhost:8000/api/v1/health")

        if response.status_code == 200:
            data = response.json()
            st.success(f"Connected successful! Server Status: {data['status']}")
            st.json(data)  # Hiển thị nội dung JSON trả về
        else:
            st.error(f"Server error: {response.status_code}")
    except Exception as e:
        st.error(f"Cannot connect to Backend: {e}")

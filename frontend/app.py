import streamlit as st
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Technical Support Chat")
st.caption("Hi, I'm your AI assistant.")

# Service selector in sidebar
with st.sidebar:
    st.header("Model Settings")
    service = st.selectbox("Service", ["rag", "chat"], index=0)
    if service == "chat":
        provider = st.selectbox("Provider", ["groq", "mistral", "hf"], index=0)
    else:
        provider = st.selectbox("Provider", ["groq", "mistral"], index=0)
    st.caption(f"Active: `{service} / {provider}`")

# Initialising history array if it doesn't exist
if 'history' not in st.session_state:
    st.session_state.history = []

# Display chat history. Support legacy string entries by falling back to a default role/content.
for i, message in enumerate(st.session_state.history):
    if isinstance(message, dict):
        role = message.get("role", "user")
        content = message.get("content", "")
    else:
        role = "user"
        content = str(message)
    with st.chat_message(role):
        st.write(content)
        
# Function for stream response.
def chat_stream(prompt):
    for char in prompt:
        yield char
        time.sleep(0.02)

# Input box for user prompt. On each input the prompt is added to the history and displayed in the chat interface.
if prompt := st.chat_input("Enter your message:"):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.history.append({"role": "user", "content": prompt})


    # Call backend API — always send chat history for memory
    history = st.session_state.history[:-1]  # exclude current user message
    payload = {"prompt": prompt, "provider": provider, "history": history}
    endpoint = f"{BACKEND_URL}/rag" if service == "rag" else f"{BACKEND_URL}/chat"

    backend_response = None
    used_service = service
    used_provider = provider

    try:
        with st.spinner("Thinking..."):
            response = requests.post(endpoint, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            backend_response = data.get("response", "")
            used_service = data.get("service", service)
            used_provider = data.get("provider", provider)
    except requests.exceptions.ConnectionError:
        backend_response = "Error: Could not connect to the backend. Make sure the server is running."
    except requests.exceptions.Timeout:
        backend_response = "Error: The request timed out. The backend may be overloaded."
    except requests.exceptions.HTTPError as e:
        backend_response = f"Error: Backend returned an unexpected response ({e.response.status_code})."
    except Exception as e:
        backend_response = f"Error: {str(e)}"

    # Stream the assistant response while capturing the full text
    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""
        for ch in chat_stream(backend_response):
            response_text += ch
            placeholder.write(response_text)
        st.caption(f"via `{used_service} / {used_provider}`")

    st.session_state.history.append({"role": "assistant", "content": response_text})
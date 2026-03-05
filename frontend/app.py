import streamlit as st
import time
import requests as req

st.title("Test Chat")

# Service selector in sidebar
with st.sidebar:
    st.header("Model Settings")
    service = st.selectbox("Service", ["chat", "rag"], index=0)
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
        
# Function for stream response. In a real implementation, this would call the backend API and stream the response as it arrives.
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
    endpoint = "http://localhost:8000/rag" if service == "rag" else "http://localhost:8000/chat"
    response = req.post(endpoint, json=payload)
    if response.status_code == 200:
        data = response.json()
        backend_response = data.get("response", "")
        used_service = data.get("service", service)
        used_provider = data.get("provider")

    # Stream the assistant response while capturing the full text
    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""
        for ch in chat_stream(backend_response):
            response_text += ch
            placeholder.write(response_text)
        st.caption(f"via `{used_service} / {used_provider}`")

    st.session_state.history.append({"role": "assistant", "content": response_text})
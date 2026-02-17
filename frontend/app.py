import streamlit as st
import time

st.title("Welcome to the FastAPI and Streamlit App")


# Function for stream response
def chat_stream(prompt):
    res = f'You said, "{prompt}"'
    for char in res:
        yield char
        time.sleep(0.02)

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

# Input box for user prompt. On each input the prompt is added to the history and displayed in the chat interface.
if prompt := st.chat_input("Enter your message:"):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.history.append({"role": "user", "content": prompt})

    # Stream the assistant response while capturing the full text
    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""
        for ch in chat_stream(prompt):
            response_text += ch
            placeholder.write(response_text)

    st.session_state.history.append({"role": "assistant", "content": response_text})
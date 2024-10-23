import streamlit as st
import rag_chatbot_lib as glib
import random


st.set_page_config(page_title="RAG Chatbot")
st.title("RAG Chatbot [acriado-dev]")
st.subheader("Powered by Amazon Berock with Anthropic Claude v3", divider="rainbow")


@st.cache_data
def get_welcome_message() -> str:
    return random.choice(
        [
            "Hello there! How can I assist you today?",
            "Hi there! Is there anything I can help you with?",
            "Do you need help?",
        ]
    )


# UI chat history to the session cache.
# allows us to re-render the chat history to the UI as the Streamlit app is re-run with each user interaction
# Otherwise, the old messages will disappear from the user interface with each new chat message.
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "welcome_displayed" not in st.session_state:
    st.session_state.welcome_displayed = False

chat_container = st.container()
input_text = st.chat_input(
    "Chat with your bot here", key="chat_input"
)  # display a chat input box


def show_welcome_message():
    global st
    # Show welcome message only once
    if not st.session_state.welcome_displayed:
        welcome_message = get_welcome_message()
        with st.chat_message("assistant"):
            st.markdown(welcome_message)
        st.session_state.welcome_displayed = True


show_welcome_message()

if input_text:
    # Get bot response
    with st.spinner("Thinking..."):
        new_message = glib.chat_with_model(
            message_history=st.session_state.chat_history, new_text=input_text
        )

    # Add bot response to chat history
    st.session_state.chat_history.append(
        {"role": "assistant", "content": [{"text": new_message}]}
    )

    # Rerun the script to update the UI
    st.rerun()


# loop to render previous chat messages.
# Re-render previous messages based on the chat_history session state object.
# Re-render the chat history (Streamlit re-runs this script, so need this to preserve previous chat messages)
i = 0
print("[chatbot_app] --> Iterating messages...")
for message in st.session_state.chat_history:
    print(f"[chatbot_app] --> {str(i)}")
    if isinstance(message, dict):
        print("[chatbot_app] -->")
        print(message)
        message = glib.ChatMessage(
            role=message["role"], text=message["content"][0]["text"]
        )

    with chat_container.chat_message(message.role):
        st.write(message.text)
    i += 1

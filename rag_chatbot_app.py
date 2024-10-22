import streamlit as st #all streamlit commands will be available through the "st" alias
import rag_chatbot_lib as glib #reference to local lib script
import random


st.set_page_config(page_title="RAG Chatbot") #HTML title
st.title("RAG Chatbot") #page title
st.subheader("Powered by Amazon Berock with Anthropic Claude v2",
             divider="rainbow")

@st.cache_data
def get_welcome_message() -> str:
    return random.choice(
        [
            "Hello there! How can I assist you today?",
            "Hi there! Is there anything I can help you with?",
            "Do you need help?",
        ]
    )

#UI chat history to the session cache.
#allows us to re-render the chat history to the UI as the Streamlit app is re-run with each user interaction
#Otherwise, the old messages will disappear from the user interface with each new chat message.
if 'chat_history' not in st.session_state: #see if the chat history hasn't been created yet
    st.session_state.chat_history = [] #initialize the chat history

#chat input controls
#allow us to send text to the Claude 3 model for processing.
#We use the if block below to handle the user input.

chat_container = st.container()

input_text = st.chat_input("Chat with your bot here") #display a chat input box

#welcome_message = get_welcome_message()
#with st.chat_message('assistant'):
#    st.markdown(welcome_message)

if input_text:
    # Get bot response
    with st.spinner("Thinking..."):
        new_message = glib.chat_with_model(message_history=st.session_state.chat_history, new_text=input_text)

    # Add bot response to chat history
    #st.session_state.chat_history.append({"role": "assistant", "text":  new_message})

    st.session_state.chat_history.append({"role": "assistant", "content": [{"text": new_message}]})


    # Rerun the script to update the UI
    st.rerun()



#loop to render previous chat messages.
#Re-render previous messages based on the chat_history session state object.
#Re-render the chat history (Streamlit re-runs this script, so need this to preserve previous chat messages)

i = 0
print("[chatbot_app] --> Iterating messages: ")
for message in st.session_state.chat_history: #loop through the chat history
    print("[chatbot_app] -->" + str(i))
    if isinstance(message, dict):  # Check if the message is a dictionary
        print("[chatbot_app] -->")
        print(message)
        message = glib.ChatMessage(role=message['role'], text=message['content'][0]['text'])  # Convert to ChatMessage

    with chat_container.chat_message(message.role): #renders a chat line for the given role, containing everything in the with block
        st.write(message.text)  # Display the message text
    i+=1



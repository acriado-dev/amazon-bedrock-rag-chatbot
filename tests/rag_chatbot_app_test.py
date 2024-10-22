from streamlit.testing.v1 import AppTest


def test_chat_input_placeholder():
    at = AppTest.from_file("rag_chatbot_app.py").run()
    assert at.chat_input(key="chat_input").placeholder == "Chat with your bot here"


def test_welcome_message():
    at = AppTest.from_file("rag_chatbot_app.py").run()

    # Check if welcome message is displayed
    if "welcome_displayed" not in at.session_state:
        assert not at.session_state["welcome_displayed"]
        at.chat_input(key="chat_input").run()
        assert at.session_state["welcome_displayed"]


def test_chat_history_preservation():
    at = AppTest.from_file("rag_chatbot_app.py").run()

    # Check if chat history is initialized
    if "chat_history" not in at.session_state:
        assert len(at.session_state["chat_history"]) == 0

    # Simulate first user input
    at.chat_input(key="chat_input").set_value("Hello!")

    # Re-run to update chat history
    at.run()

    # Simulate second user input
    at.chat_input(key="chat_input").set_value("How are you?")

    # Re-run to update chat history
    at.run()

    # Check if second message is added
    assert len(at.session_state["chat_history"]) == 4 # Chat history contains 2 message each (user/bot)


def test_bot_response():
    at = AppTest.from_file("rag_chatbot_app.py").run()

    # Simulate user input
    at.chat_input(key="chat_input").set_value("Tell me a joke")
    at.run()

    # Check if bot has responded
    assert len(at.session_state["chat_history"]) >= 1
    assert at.session_state["chat_history"][-1]["role"] == "assistant"
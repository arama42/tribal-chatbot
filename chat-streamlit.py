from paperqa import Docs
import streamlit as st
import os
import time


def load_metadata():
    input_path = 'data/'
    file_list = os.listdir(input_path)
    print(f"directory: {input_path} number of files: {len(file_list)}")

    docs = Docs(llm='gpt-3.5-turbo')
    for filename in file_list:
        filepath = os.path.join(input_path, filename)
        docs.add(filepath)
    return docs


def app():
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "test"

    docs = load_metadata()

    def respond(message, chat_history):
        bot_message = docs.query(message)
        chat_history.append((message, bot_message.formatted_answer))
        time.sleep(2)
        return "", chat_history

    # --------------------------- interface --------------------------------#
    st.markdown(
    """
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
    )
    with st.sidebar:
        url = "https://sociology.northwestern.edu/people/faculty/core/beth-redbird-.html"
        st.title("[Redbird Lab](%s)" % url)
        st.caption("@2024")

    st.title("💬 Tribal QA")
    st.caption("An interactive question answering chatbot for Tribal Constitution.")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        response = docs.query(prompt)
        time.sleep(2)
        msg = response.formatted_answer

        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)


if __name__ == '__main__':
    app()

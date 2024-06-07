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
    st.markdown("""
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """, unsafe_allow_html=True)
    st.markdown('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">', unsafe_allow_html=True)
    st.markdown("""
    <nav class="navbar fixed-top navbar-expand-lg navbar-dark" style="background-color: #900C3F;">
      <a class="navbar-brand" href="https://www.ipr.northwestern.edu/who-we-are/faculty-experts/redbird.html" target="_blank">Redbird Lab</a>
      <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav">
          <li class="nav-item active">
            <a class="nav-link disabled" href="http://localhost:8502/" target="_self">Q&A<span class="sr-only">(current)</span></a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="http://localhost:8503/" target="_self">Upload Document</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="http://localhost:8502/" target="_self">Similarity</a>
          </li>
        </ul>
      </div>
    </nav>
    """, unsafe_allow_html=True)

    docs = load_metadata()

    def respond(message, chat_history):
        bot_message = docs.query(message)
        chat_history.append((message, bot_message.formatted_answer))
        time.sleep(2)
        return "", chat_history

    # --------------------------- interface --------------------------------#
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

import gradio as gr
import time
from paperqa import Docs
import os

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    clear = gr.ClearButton([msg, chatbot])

    input = '/Users/aparna/Desktop/KT/TribalQA/data'
    my_docs = []
    file_list = os.listdir(input)
    print(f"directory: {input} number of files: {len(file_list)}")

    for filename in file_list:
        filepath = os.path.join(input, filename)
        my_docs.append(filepath)
    print(my_docs)

    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "sk-proj-OpJot339ZhYzxzGl67UDT3BlbkFJOxlGexIVsPTsHmXuefRI"

    docs = Docs(llm='gpt-3.5-turbo')
    for d in my_docs:
        docs.add(d)
    def respond(message, chat_history):
        bot_message = docs.query(message)
        chat_history.append((message, bot_message.formatted_answer))
        time.sleep(2)
        return "", chat_history


    msg.submit(respond, [msg, chatbot], [msg, chatbot])

if __name__ == "__main__":
    demo.launch(share=True)
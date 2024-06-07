import os
import time
import re

import streamlit as st
from streamlit_text_annotation import text_annotation
from annotated_text import annotated_text
from streamlit_option_menu import option_menu
import base64
from io import StringIO
from pdfminer.high_level import extract_text

from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

st.set_page_config(layout="wide")


def displayPDF(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    # Embedding PDF in HTML
        pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'

    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)


@st.cache_resource
def init_text_summarization_model():
    # MODEL = "google/long-t5-tglobal-large"
    MODEL = "gpt2-xl"
    pipe = pipeline("summarization", model=MODEL)
    return pipe

# def get_summaries_for_paragraphs(paragraphs):

@st.cache_resource
def init_ner_pipeline():
    tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
    model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
    pipe = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple") # pass device=0 if using gpu
    return pipe


@st.cache_resource
def init_qa_pipeline():
    question_answerer_pipe = pipeline("question-answering", model='deepset/roberta-base-squad2')
    return question_answerer_pipe


@st.cache_data
def get_formatted_text_for_annotation(output):
    colour_map = {'Coreference': '#29D93B',
                  'Severity': '#FCF3CF',
                  'Sex': '#E9F7EF',
                  'Sign_symptom': '#EAF2F8',
                  'Detailed_description': '#078E8B',
                  'Date': '#F5EEF8',
                  'History': '#FDEDEC',
                  'Medication': '#F4F6F6',
                  'Therapeutic_procedure': '#A3E4D7',
                  'Age': '#85C1E9',
                  'Subject': '#D7BDE2',
                  'Biological_structure': '#AF7AC5',
                  'Activity': '#B2BABB',
                  'Lab_value': '#E6B0AA',
                  'Family_history': '#2471A3',
                  'Diagnostic_procedure': '#CCD1D1',
                  'Other_event': '#239B56',
                  'Occupation': '#B3B6B7',
                  'Time': '#B3B6B7',
                  "ORG": '#29D93B',
                  "LOC": '#AF7AC5',
                  "PER": '#f63366',
                  "MISC": '#EAF2F8',}

    annotated_texts = []
    next_index = 0
    for entity in output:
        if entity['start'] == next_index:
            #         print("found entity")
            extracted_text = text[entity['start']:entity['end']]
            #         print("annotated",annotated_text)
            annotated_texts.append((extracted_text, entity['entity_group'], colour_map[entity['entity_group']]))
        else:
            unannotated_text = text[next_index:entity['start'] - 1]
            annotated_texts.append(unannotated_text)
            extracted_text = text[entity['start']:entity['end']]
            annotated_texts.append((extracted_text, entity['entity_group'], colour_map[entity['entity_group']]))
            next_index = entity['end'] + 1

    if next_index < len(text):
        annotated_texts.append(text[next_index - 1:len(text) - 1])

    return tuple(annotated_texts)

@st.cache_data
def get_formatted_text_for_answer(text, start_pos, end_pos):
    """
    Formats the specified segment of text as an 'ANSWER' entity for annotation.

    Parameters:
    - text (str): The complete text from which the answer is extracted.
    - start_pos (int): The starting index of the answer in the text.
    - end_pos (int): The ending index of the answer in the text.

    Returns:
    - tuple: A tuple containing segments of the text, with the answer segment
             specially formatted for annotation.
    """
    # Define the color for the 'ANSWER' entity.
    answer_color = '#FFD700'  # Gold color for highlighting the answer.

    # Initialize the list to hold text segments.
    annotated_texts = []

    # Check if there is text before the answer and add it as unannotated text.
    if start_pos > 0:
        annotated_texts.append(text[:start_pos])

    # Extract and annotate the answer segment.
    answer_text = text[start_pos:end_pos + 1]  # +1 to include the end_pos character.
    annotated_texts.append((answer_text, 'ANSWER', answer_color))

    # Check if there is text after the answer and add it as unannotated text.
    if end_pos < len(text) - 1:
        annotated_texts.append(text[end_pos + 1:])

    return tuple(annotated_texts)


@st.cache_data
def split_text_into_articles(text):
    paras = re.split(r"(\n[A-Z\s\-\(\)\,]+\n)",text)
    # print(paras[])
    for para in paras:
        # print(repr(i[:20]))
        para = re.sub("\n+"," ", para)
        para = re.sub(r" +", " ", para)
        print(len(para), repr(para))

    for _ in range(2):
        for idx in range(len(paras)-1):
            if len(paras[idx])<100:
                paras[idx+1] = paras[idx]+" "+"\n"+" "+paras[idx+1]
                paras[idx] = ""
        paragraphs = [para for para in paras if len(para)>1]
    return paragraphs


# Model initialization
pipeline_summarization = init_text_summarization_model()
pipeline_ner =init_ner_pipeline()
pipeline_qa = init_qa_pipeline()

st.header("Tribal Document")


with st.sidebar:
    selected_menu = option_menu("Select Option",
                                ["Upload Document", "Extract Text", "Summarize Sections", "Extract Entities",
                                 "Get Answers"],
                                menu_icon="cast", default_index=0)
    #"Annotation Tool","Claim Status Report","Detected Barriers"

uploaded_file = None

if selected_menu == "Upload Document":
    uploaded_file = st.file_uploader("Upload a legal doc", type="pdf")
    st.session_state.uploaded_file = uploaded_file
    if uploaded_file is not None:
        os.makedirs(os.path.join(os.getcwd(), "uploaded_files"), mode=0o777, exist_ok=True)
        file_path = os.path.join(os.getcwd(), "uploaded_files", uploaded_file.name)

        st.session_state.file_path = file_path

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        displayPDF(file_path)

if selected_menu == "Extract Text":
    with st.spinner("Extracting Text..."):
        uploaded_file = st.session_state.uploaded_file

        if uploaded_file is not None:
            text = extract_text(uploaded_file)
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
            paragraphs = split_text_into_articles(text)
            st.session_state.paragraphs = paragraphs

            # Display the extracted text
            st.title("Sections extracted from PDF file:")
            st.write("\n****************************\n".join(paragraphs))
        else:
            st.write("Please upload a file first")

elif selected_menu == "Summarize Sections":
    paragraphs = st.session_state.paragraphs
    if paragraphs is not None:
        # summaries = get_summaries_for_paragraphs(paragraphs)
        with st.spinner("Summarizing Document..."):

            for text in paragraphs:
                if len(text.split(" "))>150:
                    summary_text = pipeline_summarization(text, max_length=130, min_length=1, do_sample=False)
                    st.write(summary_text[0]['summary_text'])
                else:
                    st.write("ORIGINAL: ", text)
                st.markdown("""---""")
    else:
        st.write("Please extract the text first")

    # with st.spinner("Finding Topics..."):
    #     tags_found = ["Injury Details", "Past Medical Conditions", "Injury Management Plan", "GP Correspondence"]
    #     time.sleep(5)
    #     st.write("This document is about:")
    #     st.markdown(";".join(["#" + tag + " " for tag in tags_found]) + "**")
    #     st.markdown("""---""")


elif selected_menu == "Extract Entities":
    # paragraphs = get_paragraphs_for_entities()
    paragraphs = st.session_state.paragraphs

    if paragraphs is not None:
        with st.spinner("Extracting Entities..."):
            for text in paragraphs:
                output = pipeline_ner(text)
                # print("Output : ", type(output), " :::: ", output)
                entities_text = get_formatted_text_for_annotation(output)
                # print("_______________")
                # print("entities_text : ", type(entities_text), " :::: ", entities_text)
                annotated_text(*entities_text)
                st.markdown("""---""")
    else:
        st.write("Please extract the text first")

elif selected_menu == "Get Answers":
    st.subheader('Question')
    question_text = st.text_input("Type your question")
    # context = get_text_from_ocr_engine()
    paragraphs = st.session_state.paragraphs
    print(type(paragraphs))

    if question_text:
        with st.spinner("Finding Answer(s)..."):
            context = " ".join(paragraphs)
            result = pipeline_qa(question=question_text, context=context)
            st.subheader('Answer')
            st.text(result['answer'])
            st.markdown("""---""")
            st.subheader('Inline Answer')
            formatted_text = get_formatted_text_for_answer(context, result["start"], result["end"])
            annotated_text(*formatted_text)



elif selected_menu == "RAG":
    st.subheader('Question')
    question_text = st.text_input("Type your question")
    # context = get_text_from_ocr_engine()
    paragraphs = st.session_state.paragraphs
    print(type(paragraphs))

    if question_text:
        with st.spinner("Finding Answer(s)..."):
            result = pipeline_qa(question=question_text, context=" ".join(paragraphs))
            st.subheader('Answer')
            st.text(result['answer'])
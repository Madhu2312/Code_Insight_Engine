import os
import shutil
import streamlit as st
from dotenv import load_dotenv

from ingest import run_ingestion
from query import ask_question

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="Codebase RAG", layout="wide")

st.title("GitHub Codebase AI Explorer")
st.write("Paste a GitHub repository and ask questions about its code.")

if "ready" not in st.session_state:
    st.session_state.ready = False

if "answer" not in st.session_state:
    st.session_state.answer = ""

repo_url = st.text_input("Enter GitHub Repository URL")

if st.button("Index Repository"):

    if repo_url.strip() == "":
        st.warning("Please enter a valid GitHub URL")

    else:
        with st.spinner("Cloning and indexing repository..."):

            vectordb_path = os.path.join(BASE_DIR, "vectordb")
            repo_path = os.path.join(BASE_DIR, "data", "repo")
            session_file = os.path.join(BASE_DIR, "..", "current_session.txt")

            if os.path.exists(vectordb_path):
                shutil.rmtree(vectordb_path, ignore_errors=True)

            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, ignore_errors=True)

            if os.path.exists(session_file):
                os.remove(session_file)

            run_ingestion(repo_url)

        st.session_state.ready = True
        st.success("Repository indexed! You can now ask questions.")

# QUESTION SECTION
if st.session_state.ready:

    st.divider()

    with st.form("question_form"):

        question = st.text_area(
            "Type your question",
            height=140,
            placeholder="Example: How does authentication work?"
        )

        submitted = st.form_submit_button("Ask")

    if submitted:
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analyzing code..."):
                st.session_state.answer = ask_question(question)

    if st.session_state.answer:
        st.subheader("Answer")
        st.write(st.session_state.answer)
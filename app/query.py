from dotenv import load_dotenv
import os
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)

# IMPORTANT FIX
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# -------- PROJECT ROOT FIX --------
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

VECTOR_BASE = os.path.join(PROJECT_ROOT, "vectordb")
SESSION_FILE = os.path.join(PROJECT_ROOT, "current_session.txt")

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import warnings
warnings.filterwarnings("ignore")

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

def is_architecture_question(q: str) -> bool:
    q = q.lower()
    keywords = [
        "purpose",
        "what is this repository",
        "what does this project do",
        "overview",
        "architecture",
        "how are routes",
        "routing",
        "request lifecycle",
        "startup",
        "shutdown",
        "how does it work internally"
    ]
    return any(k in q for k in keywords)

def ask_question(question: str) -> str:
    """
    Main RAG answering function used by both terminal and Streamlit UI.
    """

    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    if not os.path.exists(SESSION_FILE):
        return "No repository indexed yet. Please click 'Index Repository' first."
    with open(SESSION_FILE, "r") as f:
        SESSION_PATH = f.read().strip()

    vectordb = Chroma(
        persist_directory=SESSION_PATH,
        embedding_function=embedding_model
    )

    retriever = vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 12, "fetch_k": 40}
    )

    docs = retriever.invoke(question)

    # -------- SYMBOL KEYWORD RETRIEVAL (VERY IMPORTANT) --------
    import re

    keywords = re.findall(r"[a-zA-Z_]{4,}", question.lower())

    extra_docs = []
    for kw in keywords:
        try:
            matches = vectordb.similarity_search(kw, k=2)
            extra_docs.extend(matches)
        except:
            pass

    docs = docs + extra_docs



    # ---------------- HARD GROUNDING FILTER ----------------
    behavior_keywords = [
    "how",
    "flow",
    "internally",
    "process",
    "step",
    "execution",
    "happens",
    "trace",
    "when"
]

    if any(k in question.lower() for k in behavior_keywords):
         docs = [d for d in docs if d.metadata.get("doc_type") != "repo_description"]
    # -------- IMPORTANCE FILTER --------
    filtered_docs = []
    for d in docs:
        if d.metadata.get("importance", "medium") != "low":
            filtered_docs.append(d)

    if filtered_docs:
        docs = filtered_docs

    

    # -------- GROUP BY FILE (REAL FIX) --------
    from collections import defaultdict

    file_groups = defaultdict(list)

    for d in docs:
        src = d.metadata.get("source", "unknown")
        file_groups[src].append(d.page_content)

    context_blocks = []

# take most relevant 3 files instead of random chunks
    for file, contents in list(file_groups.items())[:3]:
        merged = "\n\n".join(contents)[:2500]
        block = f"\nFILE: {file}\n{merged}"
        context_blocks.append(block)

    context = "\n\n----------------------\n\n".join(context_blocks)

    

    groq_key = None


    if "GROQ_API_KEY" in st.secrets:
        groq_key = st.secrets["GROQ_API_KEY"]


    if not groq_key:
        groq_key = os.getenv("GROQ_API_KEY")


    if not groq_key:
        return "ERROR: GROQ_API_KEY not found in Streamlit secrets or environment."

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
        groq_api_key=groq_key
    )

    prompt = f"""
You are analyzing source code.

Rules:
- Only describe behavior directly supported by the code.
- Do not assume execution order.
- Do not invent call chains.
- Mention specific functions and classes found in the files.
- If a relationship is not visible, say: "Not visible in the provided code."

Focus on evidence, not storytelling.

Code:
{context}

Question:
{question}
"""

    response = llm.invoke(prompt)
    return response.content


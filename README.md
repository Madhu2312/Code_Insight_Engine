# 🚀 Code_Insight_Engine

**AI-Powered Codebase Understanding using Retrieval-Augmented Generation (RAG)**

Code Insight Engine is an intelligent system that can read an unfamiliar GitHub repository and answer questions about how the software works internally.

Instead of manually exploring hundreds of files, developers can paste a repository link and ask questions such as:

* *What does this project do?*
* *How does authentication work?*
* *Where is a token verified?*
* *What is the execution flow?*

The system analyzes real source code and produces explanations grounded directly in the repository.

---

## ✨ Key Features

* Clone and analyze any public GitHub repository
* Automatic Python code parsing using AST
* Extracts classes, functions, decorators and relationships
* Understands internal execution flow
* Explains architecture using AI
* Answers developer questions about the codebase
* Web interface for interactive Q&A
* Grounded answers (not generic ChatGPT explanations)

---

## 🧠 How It Works (Architecture)

The project implements a **Retrieval-Augmented Generation (RAG) pipeline** for software understanding.

### Step-by-Step Pipeline

1. User enters a GitHub repository URL
2. Repository is cloned locally
3. Python files are discovered
4. AST parsing extracts:

   * functions
   * classes
   * decorators
   * call relationships
5. Code chunks are converted into embeddings
6. Stored inside a Chroma vector database
7. User asks a question
8. Relevant code is retrieved
9. LLM generates an explanation grounded in retrieved code

---

## 🏗️ System Components

### 1. Code Ingestion (`ingest.py`)

* Clones repository
* Parses Python files
* Extracts symbols via AST
* Builds vector database

### 2. Query Engine (`query.py`)

* Retrieves relevant code
* Filters irrelevant files
* Builds grounded prompt
* Uses LLM to explain behavior

### 3. Web Interface (`streamlit_app.py`)

* User inputs repository
* Indexes project
* Interactive Q&A system

---

## 🛠️ Technologies Used

### AI & Retrieval

* Retrieval Augmented Generation (RAG)
* LLaMA 3 (Groq API)
* LangChain

### Code Analysis

* Python AST (Abstract Syntax Tree)
* Static code analysis
* Call-relation extraction

### Embeddings & Storage

* SentenceTransformers (all-MiniLM-L6-v2)
* Chroma Vector Database

### Backend & UI

* Python
* Streamlit

### Utilities

* GitPython (repository cloning)
* dotenv environment configuration

---

## 📦 Installation

### 1. Clone this project

```bash
git clone https://github.com/Madhu2312/code-insight-engine.git
cd code-insight-engine
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/Mac**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Setup

Create a `.env` file in the root directory:

```
GROQ_API_KEY=your_groq_api_key_here
```

You can get a free API key from:
https://console.groq.com/

---

## ▶️ Running the Application

Start the web interface:

```bash
streamlit run app/streamlit_app.py
```

Then open the browser:

```
http://localhost:8501
```

---

## 🧪 Example Usage

1. Paste a GitHub repository URL
2. Click **Index Repository**
3. Wait 1–3 minutes (initial parsing)
4. Ask questions like:

* What is the purpose of this repository?
* Where is authentication handled?
* How are tokens verified?
* What is the execution flow?
* Which function creates a response object?

---

## 📁 Project Structure

```
code-insight-engine/
│
├── app/
│   ├── ingest.py
│   ├── query.py
│   └── streamlit_app.py
│
├── data/              # cloned repositories
├── vectordb/          # embeddings storage
├── .env
├── current_session.txt
├── requirements.txt
└── README.md
```

---

## 🎯 Problem Solved

Large repositories are difficult to understand for new developers.
Manual onboarding requires reading hundreds of files.

Code Insight Engine automatically analyzes the codebase and explains:

* architecture
* execution flow
* responsibilities of modules
* internal behavior

This significantly reduces developer onboarding and code review effort.

---

## ⚠️ Limitations

* Currently supports Python repositories only
* First indexing may take a few minutes
* Extremely large repositories may take longer to embed

---

## 🔮 Future Improvements

* Multi-language support (JavaScript, Java, Go)
* Dependency graph visualization
* Code summarization reports
* VS Code extension
* Local LLM support

---

## 👨‍💻 Author

**P Madhu**
B.Tech Computer Science and Engineering

---

## 📜 License

This project is for educational and research purposes.

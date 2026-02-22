# ======================= CODEBASE RAG INGEST (FINAL) =======================

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
import os
load_dotenv()
import json
import shutil
import stat
import uuid
import time
import ast

from git import Repo
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
# -------- PROJECT ROOT FIX --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

DATA_PATH = os.path.join(PROJECT_ROOT, "data")
REPO_PATH = os.path.join(DATA_PATH, "repo")
VECTOR_BASE = os.path.join(PROJECT_ROOT, "vectordb")
SESSION_FILE = os.path.join(PROJECT_ROOT, "current_session.txt")

SESSION_TTL = 60 * 60 * 24  # 24 hours

# ---------------- WINDOWS SAFE DELETE ----------------

def force_delete(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

# ---------------- CLEAN OLD SESSIONS ----------------

def cleanup_old_sessions():
    if not os.path.exists(VECTOR_BASE):
        return

    now = time.time()

    for folder in os.listdir(VECTOR_BASE):
        path = os.path.join(VECTOR_BASE, folder)
        if not os.path.isdir(path):
            continue

        created = os.path.getmtime(path)
        if now - created > SESSION_TTL:
            print(f"Deleting expired session: {folder}")
            shutil.rmtree(path, ignore_errors=True)

# ---------------- CLONE REPO ----------------

from git import Repo, GitCommandError

def clone_repo(repo_url):
    if os.path.exists(REPO_PATH):
        print("Removing old repository...")
        shutil.rmtree(REPO_PATH, onerror=force_delete)

    print("Cloning repository...")

    try:
        Repo.clone_from(repo_url, REPO_PATH)
        print("Repository downloaded successfully!")
        return True

    except GitCommandError as e:
        print("\nERROR: Unable to clone repository.")
        print("Possible reasons:")
        print("- Repository does not exist")
        print("- Repository is private")
        print("- Wrong URL format")
        print("- GitHub rate limited the request")

        if os.path.exists(REPO_PATH):
            shutil.rmtree(REPO_PATH, ignore_errors=True)

        return False

    except Exception as e:
        print("\nUnexpected error while cloning:", str(e))
        return False
# ---------------- FILE FILTER ----------------

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".idea",
    ".vscode",
    "tests",
    "test",
    "examples",
    "docs",
    "documentation",
    "migrations",
    "dist",
    "build",
    ".github"
}

def get_python_files():
    code_files = []

    for root, dirs, files in os.walk(REPO_PATH):
        dirs[:] = [d for d in dirs if d.lower() not in IGNORE_DIRS]

        for file in files:
            if file.endswith(".py"):
                code_files.append(os.path.join(root, file))

    return code_files

# ---------------- IMPORTANCE CLASSIFICATION ----------------
def classify_importance(path: str):
    """
    Assign importance weight to code.
    Focus on execution flow files (routing, app lifecycle).
    """
    p = path.lower()

    # ignore junk first
    LOW_PRIORITY = [
        "tests",
        "test_",
        "examples",
        "example",
        "tutorial",
        "docs",
        "benchmarks",
        "demo",
        "cli.py",
        "testing.py"
    ]

    if any(x in p for x in LOW_PRIORITY):
        return "low"

    # routing + lifecycle engine (CRITICAL FILES)
    HIGH_PRIORITY = [
        "app.py",
        "routing",
        "router",
        "blueprint",
        "views.py",
        "application",
        "wsgi",
        "asgi"
    ]

    if any(x in p for x in HIGH_PRIORITY):
        return "high"

    # everything else
    return "medium"

# ---------------- AST SYMBOL EXTRACTION ----------------
def extract_call_relations(tree, source, file_path):
    """
    Extract function call relationships (THE MISSING PIECE).
    This lets the AI understand execution flow.
    """
    documents = []

    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):

            try:
                start = node.lineno - 1
                end = min(start + 3, len(lines))  # capture small context

                code = "\n".join(lines[start:end])

                # identify called function name
                func_name = ""

                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id

                if func_name == "":
                    continue

                documents.append(
                    Document(
                        page_content=code,
                        metadata={
                            "source": file_path,
                            "file_name": os.path.basename(file_path),
                            "symbol_name": f"CALL->{func_name}",
                            "symbol_type": "call_relation",
                            "importance": "high"
                        }
                    )
                )
            except:
                pass

    return documents
def extract_symbols(file_path):
    documents = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
            # -------- PROJECT ENTRYPOINT DETECTION (VERY IMPORTANT) --------
        if '__name__ == "__main__"' in source or "__name__ == '__main__'" in source:
            documents.append(
            Document(
                page_content=source,
                metadata={
                    "source": file_path,
                    "file_name": os.path.basename(file_path),
                    "symbol_name": "PROJECT_ENTRYPOINT",
                    "symbol_type": "entrypoint",
                    "importance": "high",
                    "doc_type": "project_entry"
                }
        )
        )

        tree = ast.parse(source)
        # -------- ADD CALL RELATION EXTRACTION --------
        documents.extend(extract_call_relations(tree, source, file_path))

        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef):

                start = node.lineno - 1
                end = node.end_lineno

    # -------- DECORATOR CAPTURE (CRITICAL FIX) --------
                decorators = []
                for d in node.decorator_list:
                    decorators.append(ast.get_source_segment(source, d))

                function_code = "\n".join(source.splitlines()[start:end])

    # prepend decorators
                if decorators:
                    function_code = "\n".join(decorators) + "\n" + function_code

                code = function_code

                documents.append(
                    Document(
                        page_content=code,
                        metadata={
                            "source": file_path,
                            "file_name": os.path.basename(file_path),
                            "symbol_name": node.name,
                            "symbol_type": "function",
                            "importance": classify_importance(file_path)
                        }
                    )
                )

            elif isinstance(node, ast.ClassDef):
                start = node.lineno - 1
                end = node.end_lineno
                code = "\n".join(source.splitlines()[start:end])

                documents.append(
                    Document(
                        page_content=code,
                        metadata={
                            "source": file_path,
                            "file_name": os.path.basename(file_path),
                            "symbol_name": node.name,
                            "symbol_type": "class",
                            "importance": classify_importance(file_path)
                        }
                    )
                )

        # module summary chunk
        documents.append(
            Document(
                page_content=source,
                metadata={
                    "source": file_path,
                    "file_name": os.path.basename(file_path),
                    "symbol_name": "FULL_FILE",
                    "symbol_type": "module",
                    "importance": classify_importance(file_path)
                }
            )
        )

    except Exception:
        pass

    return documents

# ---------------- LOAD DOCUMENTS ----------------
def load_repo_documents():
    repo_docs = []

    important_files = ["README.md", "readme.md", "pyproject.toml", "setup.py"]

    for root, _, files in os.walk(REPO_PATH):
        for file in files:
            if file in important_files:
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # detect entrypoint files
                    symbol_type = "repo_doc"
                    importance = "high"
                    doc_type = "repo_description"

                    if file in ["pyproject.toml", "setup.py"]:
                        symbol_type = "entrypoint"
                        importance = "critical"
                        doc_type = "project_entry"

                    repo_docs.append(
                        Document(
                            page_content=content,
                            metadata={
                                    "source": path,
                                    "file_name": file,
                                    "symbol_name": "PROJECT_ENTRYPOINT",
                                    "symbol_type": symbol_type,
                                    "importance": importance,
                                    "doc_type": doc_type
                                }
                            )
                        )
                except:
                    pass

    return repo_docs
def load_documents(files):
    all_docs = []

    # code symbols
    for file in files:
        docs = extract_symbols(file)
        all_docs.extend(docs)

    # repository description (CRITICAL)
    repo_docs = load_repo_documents()
    all_docs.extend(repo_docs)

    return all_docs
# ---------------- VECTOR DB ----------------

def create_session_db(chunks):
    cleanup_old_sessions()

    session_id = str(uuid.uuid4())[:8]
    session_path = os.path.join(VECTOR_BASE, f"session_{session_id}")
    os.makedirs(VECTOR_BASE, exist_ok=True)

    print(f"\nCreating session memory: {session_path}")

    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=session_path
    )

    vectordb.persist()

    with open(SESSION_FILE, "w") as f:
        f.write(session_path)

    print("Session ready and stored.")

# ---------------- MAIN ----------------


def run_ingestion(repo_link):

    success = clone_repo(repo_link)
    if not success:
        return

    files = get_python_files()
    print(f"\nPython files discovered: {len(files)}")

    docs = load_documents(files)
    print(f"Code symbols extracted: {len(docs)}")

    print("\nCreating embeddings...")
    create_session_db(docs)

    print("\nEmbeddings stored successfully!")


if __name__ == "__main__":
    repo_link = input("Enter GitHub repository URL: ")
    run_ingestion(repo_link)
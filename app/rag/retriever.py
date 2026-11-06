from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.loader import load_knowledge_documents
from app.rag.embeddings import get_embeddings


VECTORSTORE_DIR = Path("data/vectorstore")


def build_vectorstore():
    documents = load_knowledge_documents()

    if not documents:
        raise RuntimeError(
            "No knowledge documents found in data/knowledge/"
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    embeddings = get_embeddings()

    vectorstore = FAISS.from_documents(
        chunks,
        embeddings
    )

    VECTORSTORE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    vectorstore.save_local(
        str(VECTORSTORE_DIR)
    )

    return vectorstore


def load_vectorstore():
    embeddings = get_embeddings()

    if not VECTORSTORE_DIR.exists():
        return build_vectorstore()

    return FAISS.load_local(
        str(VECTORSTORE_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )


def search_knowledge(query: str, k: int = 3):
    vectorstore = load_vectorstore()

    results = vectorstore.similarity_search(
        query,
        k=k
    )

    return results
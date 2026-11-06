from pathlib import Path
from langchain_core.documents import Document


KNOWLEDGE_DIR = Path("data/knowledge")


def load_knowledge_documents():
    documents = []

    for file_path in KNOWLEDGE_DIR.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": file_path.name,
                    "type": "knowledge_base"
                }
            )
        )

    return documents
import logging
import os
import threading
import uuid

from llm.dashscope_client import dashscope_embedding


logger = logging.getLogger(__name__)

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vector_db")
COLLECTION_NAME = os.getenv("VECTOR_COLLECTION_NAME", "documents")

_vector_db_client = None
_lock = threading.Lock()


def get_vector_db_client():
    global _vector_db_client
    if _vector_db_client is not None:
        return _vector_db_client

    with _lock:
        if _vector_db_client is not None:
            return _vector_db_client

        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(
            path=VECTOR_DB_PATH,
            settings=Settings(allow_reset=False, anonymized_telemetry=False),
        )
        if COLLECTION_NAME not in [c.name for c in client.list_collections()]:
            client.create_collection(COLLECTION_NAME)
            logger.info("Created collection: %s", COLLECTION_NAME)
        _vector_db_client = client
        return client


def get_collection():
    return get_vector_db_client().get_collection(COLLECTION_NAME)


def save_documents_to_vector_db(texts: list[str], category: str = "default") -> None:
    if not texts:
        return
    cleaned_texts = [item.strip() for item in texts if item and item.strip()]
    if not cleaned_texts:
        return

    vectors = dashscope_embedding(cleaned_texts)
    ids = [f"doc_{uuid.uuid4()}" for _ in cleaned_texts]
    metadatas = [{"category": category} for _ in cleaned_texts]
    collection = get_collection()
    collection.add(
        documents=cleaned_texts,
        embeddings=vectors,
        metadatas=metadatas,
        ids=ids,
    )


def query_vector_db(query_text: str, top_k: int = 3) -> list[str]:
    if not query_text.strip():
        return []
    query_vector = dashscope_embedding([query_text])[0]
    collection = get_collection()
    results = collection.query(query_embeddings=[query_vector], n_results=top_k)
    return [doc for doc in results["documents"][0]] if results["documents"] else []

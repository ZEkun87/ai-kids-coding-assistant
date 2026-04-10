"""Deprecated module - use rag/vector_store.py instead.

This module uses old LangChain imports that are incompatible with current setup.
DO NOT USE - Delete when refactoring complete.
"""

# from langchain_community.vectorstores import Chroma
# from langchain_community.embeddings import DashScopeEmbeddings

# Forward to new implementation
from backend.rag.vector_store import get_vector_store

print("WARNING: embedding_service.py is deprecated. Use rag/vector_store.py instead.")

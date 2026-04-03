def retrieve_node(state: dict):
    question = state["question"]
    from rag.chroma_store import query_vector_db

    docs = query_vector_db(question, top_k=3)

    return {**state, "documents": docs}

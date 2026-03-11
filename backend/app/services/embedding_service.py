# backend/app/services/embedding_service.py
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# 初始化向量数据库
embeddings = OpenAIEmbeddings()
vectordb = Chroma(persist_directory="./vector_db", embedding_function=embeddings)

# 保存文档
def save_documents_to_vector_db(texts, category="default"):
    metadatas = [{"category": category} for _ in texts]
    vectordb.add_texts(texts=texts, metadatas=metadatas)
    vectordb.persist()

# 查询
def query_vector_db(question, category=None, k=5):
    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    if category:
        retriever.search_kwargs["filter"] = {"category": category}
    return retriever
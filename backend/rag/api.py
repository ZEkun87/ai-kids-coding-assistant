from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .rag_engine import ask_rag  # 相对导入

router = APIRouter()

class RAGRequest(BaseModel):
    question: str
    category: str = "default"

@router.post("/rag-ask")
def rag_ask(request: RAGRequest):
    response = ask_rag(request.question, category=request.category)

    if response.get("code") != 0:
        raise HTTPException(status_code=500, detail=response.get("message", "RAG 查询失败"))

    data = response.get("data", {})
    return {
        "answer": data.get("answer", ""),
        "sources": data.get("sources", [])
    }

@router.get("/test")
def test_rag():
    return {"message": "RAG API OK"}
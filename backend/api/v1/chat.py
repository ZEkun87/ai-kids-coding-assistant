import uuid

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from models.chat import get_history
from service.qa_service import (
    analyze_code,
    ask_question,
    ask_stream_lines,
    generate_exercise,
    upload_and_index,
)


router = APIRouter()


class QuestionRequest(BaseModel):
    question: str
    category: str = "default"


class CodeRequest(BaseModel):
    code: str


class TopicRequest(BaseModel):
    topic: str


@router.post("/ask")
def ask_question_endpoint(request: QuestionRequest):
    request_id = str(uuid.uuid4())
    result = ask_question(request.question, request.category)
    return {
        "answer": result["answer"],
        "request_id": request_id,
        "sources": result["sources"],
        "intent": result["intent"],
    }


@router.post("/analyze")
def analyze_code_endpoint(request: CodeRequest):
    return {"analysis": analyze_code(request.code)}


@router.post("/exercise")
def generate_exercise_endpoint(request: TopicRequest):
    return {"exercise": generate_exercise(request.topic)}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), category: str = Query("default")):
    return await upload_and_index(file=file, category=category)


@router.get("/history")
def get_history_endpoint(category: str | None = None, limit: int = 20):
    return get_history(category=category, limit=limit)


@router.post("/ask-stream")
def ask_stream(request: QuestionRequest):
    return StreamingResponse(
        ask_stream_lines(request.question), media_type="text/event-stream"
    )

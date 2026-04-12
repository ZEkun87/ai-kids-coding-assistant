import uuid
from typing import List, Optional

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from models.chat import get_history
from service.qa_service import (
    analyze_code,
    ask_question,
    ask_stream_lines,
    generate_exercise,
    ocr_code_analyze,
    speech_to_text,
    upload_and_index,
)


router = APIRouter()


class HistoryItem(BaseModel):
    role: str
    content: str


class QuestionRequest(BaseModel):
    question: str
    history: List[HistoryItem] = []
    category: str = "default"


class CodeRequest(BaseModel):
    code: str


class TopicRequest(BaseModel):
    topic: str


@router.post("/ask")
def ask_question_endpoint(request: QuestionRequest):
    request_id = str(uuid.uuid4())
    # Pydantic v2 compatibility: use model_dump() instead of dict()
    history = [item.model_dump() for item in request.history]
    result = ask_question(request.question, history, request.category)
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
def get_history_endpoint(category: Optional[str] = None, limit: int = 20):
    return get_history(category=category, limit=limit)


@router.post("/ask-stream")
def ask_stream(request: QuestionRequest):
    async def generate_sse_events():
        """Wrap streaming response in SSE format."""
        for line in ask_stream_lines(request.question):
            # SSE format: data: {line}\n\n
            yield f"data: {line}\n\n"

    return StreamingResponse(generate_sse_events(), media_type="text/event-stream")


@router.post("/ocr-code-analyze")
async def ocr_code_analyze_endpoint(file: UploadFile = File(...)):
    return await ocr_code_analyze(file=file)


@router.post("/speech-to-text")
async def speech_to_text_endpoint(file: UploadFile = File(...)):
    """Convert speech audio to text."""
    return await speech_to_text(file=file)

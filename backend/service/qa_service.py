import io
import logging
import time
import uuid

from docx import Document
from fastapi import HTTPException, UploadFile
from PyPDF2 import PdfReader

from agent.runner import run_agent
from llm.dashscope_client import call_dashscope
from models.chat import save_chat
from rag.chroma_store import query_vector_db, save_documents_to_vector_db


logger = logging.getLogger(__name__)


def ask_question(question: str, category: str = "default") -> dict:
    request_id = str(uuid.uuid4())
    logger.info("[ask] request_id=%s question=%s category=%s", request_id, question, category)
    result = run_agent(question)
    answer = result.get("final_answer") or result.get("answer") or "暂无回答"
    docs = result.get("documents") or []
    save_chat(question, answer, category)
    logger.info(
        "[ask] request_id=%s intent=%s docs=%s",
        request_id,
        result.get("intent"),
        len(docs),
    )
    return {"answer": answer, "sources": docs}


def analyze_code(code: str) -> str:
    prompt = f"""
分析以下少儿Python代码：{code}
要求：1. 指出语法错误/逻辑问题；2. 给出简单修改建议；3. 用少儿能懂的语言解释。
"""
    return call_dashscope(prompt, temperature=0.5)


def generate_exercise(topic: str) -> str:
    prompt = f"""
为少儿编程初学者生成关于「{topic}」的练习题：
要求：1. 难度适合小学生；2. 包含题目描述+简单提示；3. 不要给出答案。
"""
    return call_dashscope(prompt, temperature=0.8)


async def upload_and_index(file: UploadFile, category: str = "default") -> dict:
    try:
        content = await file.read()
        filename = (file.filename or "").lower()
        texts: list[str] = []

        if filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(content))
            texts = [page.extract_text() for page in reader.pages if page.extract_text()]
        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(content))
            texts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
        else:
            texts = content.decode(errors="ignore").split("\n")

        cleaned_texts = [item.strip() for item in texts if item and item.strip()]
        save_documents_to_vector_db(cleaned_texts, category)
        logger.info("Uploaded %s docs to category: %s", len(cleaned_texts), category)
        return {
            "status": "success",
            "count": len(cleaned_texts),
            "category": category,
            "msg": "文档已成功入库 RAG 知识库",
        }
    except Exception as exc:
        logger.error("File upload error: %s", exc)
        raise HTTPException(status_code=500, detail=f"文件处理失败：{exc}") from exc


def ask_stream_lines(question: str):
    request_id = str(uuid.uuid4())
    logger.info("[ask-stream] request_id=%s question=%s", request_id, question)
    try:
        result = run_agent(question)
        answer = result.get("final_answer") or result.get("answer") or "暂无回答"
        for line in answer.split("\n"):
            if line.strip():
                yield line + "\n"
                time.sleep(0.05)
    except Exception as exc:
        logger.error("流式回答失败：%s request_id=%s", exc, request_id)
        yield "抱歉，回答生成失败，请稍后再试～\n"

"""
少儿编程智能辅导系统 - QA Service Module
==========================================
Author: 少儿编程智能辅导系统开发团队
License: Non-Commercial Use License
Copyright (c) 2024 All Rights Reserved
Watermark: KIDS_CODING_TUTOR_2024_AUTHORIZED
"""

import io
import logging
import re
import time
import uuid

from docx import Document
from fastapi import HTTPException, UploadFile
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from PyPDF2 import PdfReader
import pytesseract

from agent.runner import run_agent
from llm.dashscope_client import call_dashscope
from models.chat import save_chat
from rag.chroma_store import query_vector_db, save_documents_to_vector_db


logger = logging.getLogger(__name__)


def _preprocess_ocr_image(image: Image.Image) -> Image.Image:
    # Improve OCR stability for code screenshots.
    gray = ImageOps.grayscale(image)
    denoised = gray.filter(ImageFilter.MedianFilter(size=3))
    contrast = ImageEnhance.Contrast(denoised).enhance(1.8)
    # Binary threshold boosts text-background separation.
    return contrast.point(lambda p: 255 if p > 155 else 0)


def _format_extracted_code_text(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    # Remove empty leading/trailing lines.
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    cleaned = []
    for line in lines:
        fixed = line.replace("\t", "    ")
        fixed = (
            fixed.replace("，", ",")
            .replace("：", ":")
            .replace("（", "(")
            .replace("）", ")")
        )
        fixed = (
            re.sub(r"[ ]{2,}", " ", fixed) if fixed.lstrip().startswith("#") else fixed
        )
        cleaned.append(fixed)
    return "\n".join(cleaned).strip()


def _build_contextual_question(question: str, history: list[dict]) -> str:
    if not history:
        return question

    formatted_history = []
    for item in history[-6:]:
        role = "用户" if item.get("role") == "user" else "助手"
        formatted_history.append(f"{role}: {item.get('content', '')}")

    history_text = "\n".join(formatted_history)
    return f"以下是之前的对话历史：\n{history_text}\n\n用户继续提问：{question}"


def ask_question(
    question: str, history: list[dict] | None = None, category: str = "default"
) -> dict:
    history = history or []
    contextual_question = _build_contextual_question(question, history)
    request_id = str(uuid.uuid4())
    logger.info(
        "[ask] request_id=%s question=%s category=%s", request_id, question, category
    )
    result = run_agent(contextual_question)
    answer = result.get("final_answer") or result.get("answer") or "暂无回答"
    docs = result.get("documents") or []
    intent = result.get("intent", "qa")
    save_chat(question, answer, category)
    logger.info(
        "[ask] request_id=%s intent=%s docs=%s",
        request_id,
        intent,
        len(docs),
    )
    return {"answer": answer, "sources": docs, "intent": intent}


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
            texts = [
                page.extract_text() for page in reader.pages if page.extract_text()
            ]
        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(content))
            texts = [
                paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()
            ]
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


async def ocr_code_analyze(file: UploadFile) -> dict:
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        preprocessed = _preprocess_ocr_image(image)
        extracted_text = pytesseract.image_to_string(
            preprocessed,
            lang="eng",
            config="--oem 3 --psm 6",
        )
        extracted_text = _format_extracted_code_text(extracted_text)
        if not extracted_text:
            raise HTTPException(
                status_code=400, detail="未识别到可用文本，请换一张更清晰的代码截图。"
            )

        analysis = analyze_code(extracted_text)
        return {"extracted_text": extracted_text, "analysis": analysis}
    except HTTPException:
        raise
    except pytesseract.TesseractNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="OCR 依赖未安装：请先安装 tesseract（macOS: brew install tesseract）。",
        ) from exc
    except Exception as exc:
        logger.error("OCR code analyze failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"OCR 识别失败：{exc}") from exc


async def speech_to_text(file: UploadFile) -> dict:
    """Convert speech audio to text using DashScope ASR API."""
    try:
        content = await file.read()
        filename = (file.filename or "").lower()

        # Validate file format - support webm from browser recording
        if not any(
            filename.endswith(ext)
            for ext in [".wav", ".mp3", ".m4a", ".aac", ".flac", ".webm", ".ogg"]
        ):
            raise HTTPException(
                status_code=400,
                detail="不支持的音频格式，请使用 wav/mp3/m4a/aac/flac/webm/ogg 格式。",
            )

        # Use DashScope ASR service for speech recognition
        from llm.dashscope_client import transcribe_audio

        text = transcribe_audio(content, filename)

        if not text or not text.strip():
            raise HTTPException(
                status_code=400, detail="未能识别到语音内容，请检查音频文件是否清晰。"
            )

        logger.info("Speech recognized successfully, length: %d", len(text))
        return {"text": text.strip()}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Speech to text failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"语音识别失败：{exc}") from exc

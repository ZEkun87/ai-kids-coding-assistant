import hashlib
import logging
import os

import dashscope
from dashscope import Generation, TextEmbedding
from fastapi import HTTPException


logger = logging.getLogger(__name__)


def _ensure_dashscope_api_key() -> None:
    # Refresh api key on each call so import order does not break auth.
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if api_key:
        dashscope.api_key = api_key


def call_dashscope(prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
    try:
        _ensure_dashscope_api_key()
        response = Generation.call(
            model="qwen-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            result_format="text",
        )
        text = getattr(response.output, "text", None)
        if text is None and hasattr(response.output, "__iter__"):
            text = " ".join([getattr(item, "text", "") for item in response.output])
        if text is None:
            text = str(response.output)
        return text.strip()
    except Exception as exc:
        logger.error("DashScope API error: %s", exc)
        raise HTTPException(status_code=500, detail=f"通义千问调用失败：{exc}") from exc


def dashscope_embedding(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    try:
        _ensure_dashscope_api_key()
        response = TextEmbedding.call(model="text-embedding-v1", input=texts)
        return [item["embedding"] for item in response.output["embeddings"]]
    except Exception as exc:
        logger.error("Embedding 生成失败：%s", exc)
        vectors = []
        for text in texts:
            digest = int(hashlib.md5(text.encode()).hexdigest(), 16)
            vectors.append([(digest >> (idx * 8)) % 256 / 255.0 for idx in range(32)])
        return vectors

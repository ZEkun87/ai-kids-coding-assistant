import hashlib
import logging
import os
import threading
import tempfile

import dashscope
from dashscope import Generation, TextEmbedding
from fastapi import HTTPException


logger = logging.getLogger(__name__)
_lock = threading.RLock()  # Add thread lock for thread-safe API key setting


def _ensure_dashscope_api_key() -> None:
    """Ensure API key is set (thread-safe version)."""
    # Use lock to prevent race conditions in async environments
    with _lock:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if api_key:
            dashscope.api_key = api_key


def call_dashscope(
    prompt: str, temperature: float = 0.7, max_tokens: int = 1000
) -> str:
    try:
        _ensure_dashscope_api_key()
        response = Generation.call(
            model="qwen-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            result_format="text",
        )

        # Check if response is valid
        if not response:
            logger.error("DashScope response is None or empty")
            return "抱歉，AI服务暂时不可用，请稍后再试～"

        # Get the output attribute
        output = getattr(response, "output", None)
        if not output:
            logger.error("DashScope response has no output: %s", response)
            return "抱歉，AI服务返回异常，请稍后再试～"

        # Handle different response structures
        text = None

        # Try to get text from output.text attribute
        if hasattr(output, "text"):
            text = output.text

        # If output is a dict, try to get text from dict keys
        elif isinstance(output, dict):
            text = output.get("text", output.get("content", None))

        # Fallback: convert output to string
        if text is None:
            logger.warning(
                "Using fallback text extraction from output: %s", type(output)
            )
            text = str(output)

        # Clean and validate text
        text = text.strip()

        # Check if text is empty or just "None" string
        if not text or text.lower() == "none" or text == "None":
            logger.warning("DashScope returned empty or 'None' text")
            return "抱歉，AI服务未能生成回答，请稍后再试～"

        return text
    except Exception as exc:
        logger.error("DashScope API error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"通义千问调用失败：{exc}") from exc


def dashscope_embedding(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    try:
        _ensure_dashscope_api_key()
        response = TextEmbedding.call(model="text-embedding-v1", input=texts)

        # Handle different response structures
        if not response or not hasattr(response, "output") or not response.output:
            logger.warning("Embedding response has no output, using fallback vectors")
            return _fallback_embedding_vectors(texts)

        output = response.output
        if isinstance(output, dict) and "embeddings" in output:
            return [item["embedding"] for item in output["embeddings"]]
        elif isinstance(output, dict) and "results" in output:
            # Alternative response structure
            return [item["embedding"] for item in output["results"]]
        else:
            logger.warning("Unexpected embedding response structure: %s", type(output))
            return _fallback_embedding_vectors(texts)
    except Exception as exc:
        logger.error("Embedding 生成失败：%s", exc)
        return _fallback_embedding_vectors(texts)


def _fallback_embedding_vectors(texts: list[str]) -> list[list[float]]:
    """Generate deterministic fallback embedding vectors using MD5 hash."""
    vectors = []
    for text in texts:
        digest = int(hashlib.md5(text.encode()).hexdigest(), 16)
        vectors.append([(digest >> (idx * 8)) % 256 / 255.0 for idx in range(32)])
    return vectors


def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    """Transcribe audio to text using DashScope Transcription API."""
    import time
    import subprocess

    try:
        _ensure_dashscope_api_key()

        from dashscope.audio.asr import Transcription
        import requests

        # Create temporary file for audio
        original_suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=original_suffix
        ) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        # If the format is webm or ogg, convert to wav (DashScope may not support these formats well)
        actual_file_path = tmp_path
        if original_suffix.lower() in [".webm", ".ogg", ".oga"]:
            wav_path = tmp_path.replace(original_suffix, ".wav")
            try:
                logger.info(
                    "Converting %s to wav: %s -> %s",
                    original_suffix,
                    tmp_path,
                    wav_path,
                )

                # Use more robust conversion settings
                convert_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    tmp_path,
                    "-vn",  # No video
                    "-ar",
                    "16000",  # Sample rate 16kHz
                    "-ac",
                    "1",  # Mono
                    "-acodec",
                    "pcm_s16le",  # 16-bit PCM
                    "-sample_fmt",
                    "s16",  # Sample format
                    "-f",
                    "wav",  # Force WAV format
                    wav_path,
                ]

                result = subprocess.run(convert_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error("FFmpeg stderr: %s", result.stderr)
                    raise Exception(f"FFmpeg error: {result.stderr[:200]}")

                # Verify the output file
                if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
                    raise Exception("Converted WAV file is empty or not created")

                actual_file_path = wav_path
                logger.info(
                    "Conversion successful, file size: %d bytes",
                    os.path.getsize(wav_path),
                )
            except subprocess.CalledProcessError as e:
                logger.error(
                    "FFmpeg conversion failed: %s",
                    e.stderr.decode() if e.stderr else str(e),
                )
                raise HTTPException(
                    status_code=500, detail="音频格式转换失败，请尝试重新录音。"
                ) from e
            except Exception as e:
                logger.error("Audio conversion error: %s", str(e))
                raise HTTPException(
                    status_code=500, detail=f"音频处理失败：{str(e)}"
                ) from e

        max_retries = 3
        retry_delay = 2  # seconds

        try:
            for attempt in range(max_retries):
                try:
                    # Use Transcription for offline audio file recognition
                    logger.info(
                        "Calling Transcription API with file: %s (attempt %d/%d)",
                        actual_file_path,
                        attempt + 1,
                        max_retries,
                    )

                    result = Transcription.call(
                        model="paraformer-v1", file_urls=[f"file://{actual_file_path}"]
                    )

                    logger.info("Transcription result status: %s", result.status_code)
                    logger.debug("Transcription output: %s", result.output)

                    if result.status_code == 200:
                        # Extract text from response - handle different response structures
                        if hasattr(result, "output") and result.output:
                            output = result.output

                            # Log the actual structure for debugging
                            logger.info(
                                "Output type: %s, content: %s",
                                type(output).__name__,
                                output,
                            )

                            # Try different possible response structures
                            text = ""

                            # Structure 1: Direct transcripts in output (dict)
                            if isinstance(output, dict):
                                logger.info("Output keys: %s", output.keys())

                                # Check for task status first
                                task_status = output.get("task_status", "")
                                if task_status == "FAILED":
                                    error_code = output.get("code", "UNKNOWN")
                                    error_msg = output.get("message", "Unknown error")
                                    logger.error(
                                        "Transcription task failed: %s - %s",
                                        error_code,
                                        error_msg,
                                    )
                                    raise HTTPException(
                                        status_code=400,
                                        detail=f"语音识别失败：{error_msg}。请尝试使用更清晰的录音或换一种格式。",
                                    )

                                # Check for 'transcripts' key
                                if "transcripts" in output:
                                    transcripts = output["transcripts"]
                                    logger.info("Found transcripts: %s", transcripts)
                                    if isinstance(transcripts, list) and transcripts:
                                        text = transcripts[0].get("text", "")

                                # Check for 'results' key
                                elif "results" in output:
                                    results = output["results"]
                                    if isinstance(results, list) and results:
                                        text_parts = []
                                        for item in results:
                                            if isinstance(item, dict):
                                                text_parts.append(item.get("text", ""))
                                        text = " ".join(text_parts)

                                # Check for task_results (older format)
                                elif "task_results" in output:
                                    task_results = output["task_results"]
                                    if isinstance(task_results, list) and task_results:
                                        text_parts = []
                                        for task_result in task_results:
                                            if isinstance(task_result, dict):
                                                result_data = task_result.get(
                                                    "result", {}
                                                )
                                                if result_data:
                                                    sentences = result_data.get(
                                                        "sentence", []
                                                    )
                                                    for sentence in sentences:
                                                        if isinstance(sentence, dict):
                                                            text_parts.append(
                                                                sentence.get("text", "")
                                                            )
                                        text = " ".join(text_parts)

                                # If none of the above structures matched, log warning
                                if not text:
                                    logger.warning(
                                        "Could not extract text from output structure: %s",
                                        output,
                                    )

                            # Don't try to access .text attribute if output is a dict
                            # as it will cause KeyError
                            if not text and not isinstance(output, dict):
                                if hasattr(output, "text"):
                                    text = output.text

                            if text:
                                logger.info(
                                    "Transcription successful, text length: %d",
                                    len(text),
                                )
                                return text.strip()
                            else:
                                logger.warning("ASR returned empty text")
                                return ""
                        else:
                            logger.warning("No output in response")
                            return ""
                    else:
                        error_msg = getattr(result, "message", "Unknown error")
                        logger.error(
                            "ASR API error: %s - %s", result.status_code, error_msg
                        )
                        raise HTTPException(
                            status_code=500, detail=f"语音识别服务调用失败：{error_msg}"
                        )

                except requests.exceptions.SSLError as ssl_err:
                    # SSL error - retry
                    if attempt < max_retries - 1:
                        logger.warning(
                            "SSL error on attempt %d, retrying in %d seconds: %s",
                            attempt + 1,
                            retry_delay,
                            ssl_err,
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(
                            "SSL error after %d attempts: %s", max_retries, ssl_err
                        )
                        raise HTTPException(
                            status_code=500,
                            detail="语音识别服务连接失败，请检查网络连接后重试。",
                        ) from ssl_err

                except Exception as e:
                    # Other errors - don't retry, raise immediately
                    raise e
        finally:
            # Always clean up temporary files
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if actual_file_path != tmp_path and os.path.exists(actual_file_path):
                os.unlink(actual_file_path)

        # This should not be reached, but just in case
        return ""

    except HTTPException:
        raise
    except ImportError as exc:
        logger.error("DashScope ASR module not available: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="语音识别模块未安装，请更新 dashscope SDK：pip install --upgrade dashscope",
        ) from exc
    except Exception as exc:
        logger.error("Audio transcription error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"音频转文字失败：{str(exc)}"
        ) from exc

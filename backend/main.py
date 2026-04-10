"""
少儿编程智能辅导系统 - AI Kids Coding Assistant
================================================
Author: 少儿编程智能辅导系统开发团队
Version: 1.0.0
License: Non-Commercial Use License
Copyright (c) 2024 All Rights Reserved

⚠️ 重要声明: 本项目仅供学习和非商业用途使用
⚠️ IMPORTANT: This project is for learning and non-commercial use only
⚠️ 商业使用请联系作者获取授权 | For commercial use, contact the author

水印标识: KIDS_CODING_TUTOR_2024_AUTHORIZED
Watermark ID: KIDS_CODING_TUTOR_2024_AUTHORIZED
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1.chat import router as chat_router
from rag.api import router as rag_router
from models.chat import init_db
from vector_store.pgvector_store import init_vector_db


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR.parent / ".env.local")  # Load local overrides
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate required environment variables at startup
required_env_vars = ["DASHSCOPE_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Application cannot start without these variables.")
    sys.exit(1)

# Project Metadata - DO NOT REMOVE
PROJECT_METADATA = {
    "name": "少儿编程智能辅导系统",
    "name_en": "AI Kids Coding Assistant",
    "version": "1.0.0",
    "author": "少儿编程智能辅导系统开发团队",
    "license": "Non-Commercial Use License",
    "copyright": "Copyright (c) 2024 All Rights Reserved",
    "watermark_id": "KIDS_CODING_TUTOR_2024_AUTHORIZED",
    "website": "https://github.com/your-username/ai-kids-coding-assistant",
    "contact": "zekunio@outlook.com",
}

app = FastAPI(
    title="少儿编程智能辅导系统",
    description=PROJECT_METADATA["name_en"],
    version=PROJECT_METADATA["version"],
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize databases
logger.info("Initializing databases...")
try:
    init_db()  # PostgreSQL chat history
    logger.info("✅ Chat history database initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize chat database: {e}")
    sys.exit(1)

try:
    init_vector_db()  # PGVector for knowledge base
    logger.info("✅ Vector database initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize vector database: {e}")
    sys.exit(1)

# Include routers
app.include_router(chat_router, prefix="/api/v1/chat")
app.include_router(rag_router, prefix="/api/v1/rag")


# Add copyright middleware
@app.middleware("http")
async def add_copyright_header(request: Request, call_next):
    """Add copyright and watermark headers to all responses."""
    response = await call_next(request)
    response.headers["X-Project-Name"] = PROJECT_METADATA["name"]
    response.headers["X-Copyright"] = PROJECT_METADATA["copyright"]
    response.headers["X-Watermark-ID"] = PROJECT_METADATA["watermark_id"]
    response.headers["X-License"] = PROJECT_METADATA["license"]
    return response


# Log startup configuration
db_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/ai_coding_tutor")
db_url_masked = db_url.replace(os.getenv("DB_PASSWORD", "password"), "***")
logger.info("=" * 60)
logger.info("🎓 少儿编程智能辅导系统 v%s", PROJECT_METADATA["version"])
logger.info("👤 Author: %s", PROJECT_METADATA["author"])
logger.info("📜 License: %s", PROJECT_METADATA["license"])
logger.info("💧 Watermark: %s", PROJECT_METADATA["watermark_id"])
logger.info("⚠️  WARNING: Non-commercial use only!")
logger.info("=" * 60)
logger.info(
    "✅ Application started - DASHSCOPE=%s | DATABASE=%s",
    "configured",
    db_url_masked,
)


@app.get("/")
def read_root():
    return {
        "message": "少儿编程智能辅导系统运行中",
        "project": PROJECT_METADATA["name"],
        "version": PROJECT_METADATA["version"],
        "author": PROJECT_METADATA["author"],
        "license": PROJECT_METADATA["license"],
        "watermark_id": PROJECT_METADATA["watermark_id"],
        "timestamp": datetime.now().isoformat(),
        "warning": "本项目仅供学习和非商业用途 | For learning and non-commercial use only",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

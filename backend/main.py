import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.chat import router as chat_router
from models.chat import init_db


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI 少儿编程助手")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
app.include_router(chat_router)

logger.info(
    "Startup config: DASHSCOPE_API_KEY=%s, VECTOR_DB_PATH=%s",
    "configured" if os.getenv("DASHSCOPE_API_KEY") else "missing",
    os.getenv("VECTOR_DB_PATH", "./vector_db"),
)


@app.get("/")
def read_root():
    return {"message": "AI 少儿编程助手运行中"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

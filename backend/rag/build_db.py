# -*- coding: utf-8 -*-
import os
import shutil
import logging
from pathlib import Path

# 错误的旧路径
# from langchain.document_loaders import TextLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.vectorstores import Chroma
# from langchain_community.embeddings import DashScopeEmbeddings

# 正确的新路径（适配 LangChain 1.2.10）
from langchain_community.document_loaders import TextLoader  # 迁移到community
# 错误路径（删除/注释）
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# 正确路径（替换）
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma  # Chroma迁移到community
from langchain_community.embeddings import DashScopeEmbeddings  # 这个路径不变

# ================= 配置 =================

DATA_PATH = Path("data/python_docs")
PERSIST_DIR = Path("vector_db")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# ================= 日志 =================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ================= Embedding =================

"""
def get_embeddings():
    return DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=DASHSCOPE_API_KEY
    )
"""
def get_embeddings():
    return DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=DASHSCOPE_API_KEY  # 替换 dashscope_api_key 为 api_key
    )

# ================= 文档加载 =================

def load_documents():

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"数据目录不存在: {DATA_PATH}")

    documents = []

    for file in DATA_PATH.glob("*"):

        if file.suffix not in [".txt", ".md"]:
            continue

        try:

            loader = TextLoader(str(file), encoding="utf-8")

            docs = loader.load()

            documents.extend(docs)

            logger.info(f"加载成功: {file.name}")

        except Exception as e:

            logger.warning(f"加载失败 {file.name}: {e}")

    if not documents:
        raise ValueError("未找到任何可用文档")

    logger.info(f"总文档数: {len(documents)}")

    return documents


# ================= 文本切分 =================

def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,

        separators=[
            "\n\n",
            "\n",
            "。",
            " ",
            ""
        ]
    )

    docs = splitter.split_documents(documents)

    logger.info(f"文本块数量: {len(docs)}")

    return docs


# ================= 构建向量库 =================

def build_vector_db():

    # 已存在数据库则跳过
    if (PERSIST_DIR / "chroma.sqlite3").exists():

        logger.info("向量数据库已存在，跳过构建")

        return

    try:

        logger.info("开始加载文档")

        documents = load_documents()

        logger.info("开始切分文本")

        docs = split_documents(documents)

        logger.info("初始化 Embedding 模型")

        embeddings = get_embeddings()

        logger.info("开始构建向量数据库")

        vectordb = Chroma.from_documents(

            docs,
            embedding=embeddings,
            persist_directory=str(PERSIST_DIR)

        )

        #vectordb.persist()

        logger.info("向量数据库构建完成")

    except Exception as e:

        logger.error(f"构建失败: {e}")

        if PERSIST_DIR.exists():

            shutil.rmtree(PERSIST_DIR)

        raise


# ================= 主函数 =================

if __name__ == "__main__":

    if not DASHSCOPE_API_KEY:

        logger.error("请设置环境变量 DASHSCOPE_API_KEY")

    else:

        build_vector_db()

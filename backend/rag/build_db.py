# -*- coding: utf-8 -*-
# 通义千问 RAG 知识库构建脚本，适配 PyTorch 2.2.2 + LangChain 1.2.10

import os
import shutil
import logging
from pathlib import Path

# 适配 LangChain 1.2.10 的正确导入路径
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

# ================= 配置 =================
# 数据目录（确保实际存在）
DATA_PATH = Path("data/python_docs")
# 向量库存储目录
PERSIST_DIR = Path("vector_db")

# 文本切分参数
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 通义千问 Embedding API Key（从环境变量获取）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# ================= 日志配置 =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ================= Embedding 模型初始化（修复核心参数错误）=================
def get_embeddings():
    """
    初始化通义千问文本嵌入模型
    关键修复：DashScopeEmbeddings 的参数是 api_key 而非 dashscope_api_key
    """
    # 兼容 PyTorch 版本提示（可选，屏蔽无关警告）
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    return DashScopeEmbeddings(
        model="text-embedding-v1",
        api_key=DASHSCOPE_API_KEY  # 核心修复：参数名从 dashscope_api_key 改为 api_key
    )

# ================= 文档加载 =================
def load_documents():
    """加载指定目录下的 txt/md 文档"""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"数据目录不存在: {DATA_PATH}")

    documents = []
    # 递归遍历所有子目录的文档（增强兼容性）
    for file in DATA_PATH.rglob("*"):
        if file.is_file() and file.suffix in [".txt", ".md"]:
            try:
                loader = TextLoader(str(file), encoding="utf-8")
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"加载成功: {file.name}")
            except Exception as e:
                logger.warning(f"加载失败 {file.name}: {str(e)[:100]}")  # 缩短错误信息长度

    if not documents:
        raise ValueError("未找到任何可用的 txt/md 文档")

    logger.info(f"总加载文档数: {len(documents)}")
    return documents

# ================= 文本切分 =================
def split_documents(documents):
    """将长文档切分为小文本块"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],  # 补充中文分隔符
        keep_separator=False,  # 避免分隔符被单独切分
        is_separator_regex=False
    )

    docs = splitter.split_documents(documents)
    logger.info(f"文本切分完成，总文本块数量: {len(docs)}")
    return docs

# ================= 构建向量库 =================
def build_vector_db():
    """构建并持久化 Chroma 向量数据库"""
    # 检查向量库是否已存在
    if PERSIST_DIR.exists() and (PERSIST_DIR / "chroma.sqlite3").exists():
        logger.info("向量数据库已存在，跳过构建流程")
        return

    try:
        logger.info("===== 开始构建向量数据库 =====")
        
        # 1. 加载文档
        documents = load_documents()
        
        # 2. 切分文本
        docs = split_documents(documents)
        
        # 3. 初始化 Embedding 模型
        logger.info("初始化通义千问 Embedding 模型")
        embeddings = get_embeddings()
        
        # 4. 构建向量库
        logger.info("开始向量化并存储到 Chroma")
        vectordb = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=str(PERSIST_DIR),
            collection_name="python_docs"  # 指定集合名，便于管理
        )
        
        # 验证向量库构建结果
        collection = vectordb.get()
        logger.info(f"向量库构建完成！总向量数: {len(collection['ids'])}")

    except Exception as e:
        logger.error(f"构建向量库失败: {str(e)}", exc_info=False)
        # 清理失败的目录
        if PERSIST_DIR.exists():
            shutil.rmtree(PERSIST_DIR)
            logger.info("已清理失败的向量库目录")
        raise  # 抛出异常，让脚本终止

# ================= 主函数 =================
if __name__ == "__main__":
    # 检查 API Key
    if not DASHSCOPE_API_KEY:
        logger.error("❌ 请先设置环境变量 DASHSCOPE_API_KEY")
        logger.error("   示例（终端）: export DASHSCOPE_API_KEY='你的API密钥'")
    else:
        # 创建数据目录（如果不存在）
        if not DATA_PATH.exists():
            DATA_PATH.mkdir(parents=True, exist_ok=True)
            logger.warning(f"⚠️  数据目录不存在，已自动创建: {DATA_PATH}")
            logger.warning("   请将需要构建知识库的 txt/md 文件放入该目录后重新运行")
        else:
            # 执行构建
            build_vector_db()
            logger.info("===== 脚本执行完成 =====")
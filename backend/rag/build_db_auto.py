# -*- coding: utf-8 -*-
# 全自动 Python 知识库构建脚本（最终修复版，无复杂依赖）
import os
import re
import shutil
import logging
import requests
import git
import time
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# LangChain 相关导入（仅用基础库，无复杂依赖）
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document  # 新增基础 Document 类

# ================= 全局配置 =================
load_dotenv()  # 加载 .env 文件中的环境变量

# 修复路径计算：基于脚本所在目录定位项目根目录
SCRIPT_DIR = Path(__file__).resolve().parent  # backend/rag/
BACKEND_DIR = SCRIPT_DIR.parent  # backend/
PROJECT_ROOT = BACKEND_DIR.parent  # ai-coding-tutor/

# 路径配置（修复后）
RAW_DATA_PATH = PROJECT_ROOT / "data/raw_docs"  # 原始下载文档
CLEAN_DATA_PATH = PROJECT_ROOT / "data/clean_docs"  # 清洗后文档
PERSIST_DIR = PROJECT_ROOT / "vector_db/python_kb"
LOG_DIR = PROJECT_ROOT / "logs"  # 日志目录（项目根目录下）

# 文本切分配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# API 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY") or ""
MAX_WORKERS = 4  # 降低线程数，避免反爬
TIMEOUT = 30

# 文档源配置（仅保留可访问的源）
DOC_SOURCES = {
    "python_official": {
        "type": "url_list",
        "urls": [
            "https://docs.python.org/3/tutorial/index.html",
            "https://docs.python.org/3/library/functions.html",
        ],
        "save_path": RAW_DATA_PATH / "python_official"
    },
    "markdown_tutorial": {
        "type": "url",
        "url": "https://markdown-guide.readthedocs.io/zh/latest/basic.html",
        "save_path": RAW_DATA_PATH / "markdown_tutorial.html"
    },
    "python_rag_blogs": {
        "type": "url_list",
        "urls": [
            "https://juejin.cn/post/7350874104511989779",
        ],
        "save_path": RAW_DATA_PATH / "python_rag_blogs"
    }
}

# ================= 日志配置 =================
def init_logging():
    """初始化日志配置（自动创建日志目录）"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # 关键：自动创建日志目录
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "build_kb.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# 初始化日志
logger = init_logging()

# ================= 工具函数 =================
def create_dirs():
    """创建所有所需目录"""
    for dir_path in [RAW_DATA_PATH, CLEAN_DATA_PATH, PERSIST_DIR, LOG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    logger.info("所有目录初始化完成")

def clean_text(content: str) -> str:
    """清洗文本：移除多余空格、特殊字符、广告等冗余内容"""
    # 移除 HTML 标签残留
    content = re.sub(r"<[^>]+>", "", content)
    # 移除多余空白符
    content = re.sub(r"\s+", " ", content).strip()
    # 移除特殊符号
    content = re.sub(r"[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9\s\.\,\;\:\!\?\(\)\[\]\{\}]", "", content)
    # 过滤过短文本
    if len(content) < 20:
        return ""
    return content

# ================= 文档下载模块 =================
class DocumentDownloader:
    def __init__(self):
        self.session = requests.Session()
        # 完善请求头，避免反爬
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive"
        })
        # 修复：把 mount 放到 __init__ 方法内
        self.session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))

    def download_url(self, url: str, save_path: Path):
        """下载单个 URL 内容"""
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            
            # 根据内容类型自动选择保存格式
            if "text/html" in response.headers.get("Content-Type", ""):
                save_path = save_path.with_suffix(".html")
            save_path.parent.mkdir(parents=True, exist_ok=True)  # 确保父目录存在
            save_path.write_text(response.text, encoding="utf-8")
            logger.info(f"下载成功: {url} -> {save_path}")
            return True
        except Exception as e:
            logger.error(f"下载失败 {url}: {str(e)[:100]}")
            return False

    def download_url_list(self, urls: list, save_dir: Path):
        """批量下载 URL 列表（多线程）"""
        save_dir.mkdir(parents=True, exist_ok=True)
        success_count = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for i, url in enumerate(urls):
                # 生成文件名（基于 URL 哈希）
                file_name = f"doc_{i}_{hash(url) % 10000}.html"
                save_path = save_dir / file_name
                futures.append(executor.submit(self.download_url, url, save_path))
            
            # 统计结果
            for future in tqdm(as_completed(futures), total=len(futures), desc="下载 URL 列表"):
                if future.result():
                    success_count += 1
        
        logger.info(f"URL 列表下载完成：成功 {success_count}/{len(urls)}")

    def download_all_sources(self):
        """下载所有配置的文档源"""
        logger.info("===== 开始下载文档源 =====")
        
        for source_name, source_config in DOC_SOURCES.items():
            logger.info(f"处理文档源: {source_name}")
            time.sleep(1)  # 避免请求过快
            
            if source_config["type"] == "url":
                self.download_url(source_config["url"], source_config["save_path"])
            
            elif source_config["type"] == "url_list":
                self.download_url_list(source_config["urls"], source_config["save_path"])
        
        logger.info("===== 所有文档源下载完成 =====")

# ================= 文档解析与清洗模块（无 unstructured 依赖） =================
class DocumentProcessor:
    def __init__(self):
        # 仅用基础 TextLoader + 自定义 HTML 解析，无任何复杂依赖
        self.loaders = {
            ".txt": self.load_txt,
            ".md": self.load_txt,
            ".html": self.load_html_with_bs4
        }

    def load_txt(self, file_path: str):
        """加载 TXT/MD 文件"""
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()
            # 清洗内容
            for doc in docs:
                doc.page_content = clean_text(doc.page_content)
                if not doc.page_content:
                    return []
            return docs
        except Exception as e:
            logger.error(f"加载 TXT/MD 失败 {file_path}: {str(e)[:100]}")
            return []

    def load_html_with_bs4(self, file_path: str):
        """基于 BeautifulSoup 解析 HTML，无需 unstructured"""
        try:
            # 读取 HTML 文件
            html_content = Path(file_path).read_text(encoding="utf-8")
            soup = BeautifulSoup(html_content, "html.parser")
            
            # 移除无关标签
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                tag.decompose()
            
            # 提取正文（优先取 <main> <article> 标签）
            main_content = soup.find("main") or soup.find("article") or soup.body
            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)
            
            # 清洗文本
            text = clean_text(text)
            if len(text) < 20:
                return []
            
            # 返回 Document 对象
            return [Document(page_content=text, metadata={"source": file_path})]
        except Exception as e:
            logger.error(f"解析 HTML 失败 {file_path}: {str(e)[:100]}")
            return []

    def load_single_file(self, file_path: Path):
        """加载单个文件"""
        try:
            suffix = file_path.suffix.lower()
            if suffix not in self.loaders:
                logger.warning(f"不支持的格式: {file_path}")
                return []
            
            # 调用对应加载函数
            docs = self.loaders[suffix](str(file_path))
            return docs
        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {str(e)[:100]}")
            return []

    def process_all_documents(self):
        """处理所有文档"""
        logger.info("===== 开始解析与清洗文档 =====")
        all_docs = []
        file_list = list(RAW_DATA_PATH.rglob("*"))
        
        for file_path in tqdm(file_list, desc="处理文档"):
            if file_path.is_file() and file_path.suffix in [".txt", ".md", ".html"]:
                docs = self.load_single_file(file_path)
                all_docs.extend(docs)
        
        # 保存清洗后的文档
        for i, doc in enumerate(all_docs):
            save_path = CLEAN_DATA_PATH / f"clean_doc_{i}.txt"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(doc.page_content, encoding="utf-8")
        
        logger.info(f"文档处理完成：共加载 {len(all_docs)} 个有效文档")
        return all_docs

# ================= 向量库构建模块 =================
def get_embeddings():
    """初始化通义千问 Embedding 模型（兼容所有 LangChain 版本 + PyTorch 2.2.2）"""
    os.environ["TOKENIZERS_PARALLELISM"] = "false"  # 屏蔽 PyTorch 相关警告
    
    # 核心修复：兼容新版/旧版 LangChain 的参数名
    import warnings
    warnings.filterwarnings("ignore")
    
    # 优先使用 dashscope_api_key（新版 LangChain 正确参数）
    try:
        embeddings = DashScopeEmbeddings(
            model="text-embedding-v1",
            dashscope_api_key=DASHSCOPE_API_KEY
        )
    except (TypeError, ValueError):
        # 兼容旧版 api_key 参数
        embeddings = DashScopeEmbeddings(
            model="text-embedding-v1",
            api_key=DASHSCOPE_API_KEY
        )
    return embeddings

def split_documents(documents):
    """切分文档为小文本块"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        keep_separator=False,
        is_separator_regex=False
    )
    docs = splitter.split_documents(documents)
    logger.info(f"文本切分完成：共生成 {len(docs)} 个文本块")
    return docs

def build_vector_db(documents):
    """构建向量数据库"""
    if PERSIST_DIR.exists() and (PERSIST_DIR / "chroma.sqlite3").exists():
        logger.info("向量数据库已存在，跳过构建")
        return
    
    try:
        # 切分文本
        docs = split_documents(documents)
        
        # 初始化 Embedding（修复参数错误）
        logger.info("初始化通义千问 Embedding 模型...")
        embeddings = get_embeddings()
        
        # 构建向量库
        logger.info("开始构建向量数据库...")
        vectordb = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=str(PERSIST_DIR),
            collection_name="python_complete_kb"
        )
        
        # 验证结果
        collection = vectordb.get()
        logger.info(f"✅ 向量库构建完成！总向量数: {len(collection['ids'])}")
        
    except Exception as e:
        logger.error(f"❌ 构建向量库失败: {str(e)}", exc_info=True)
        if PERSIST_DIR.exists():
            shutil.rmtree(PERSIST_DIR)
        raise

# ================= 主函数 =================
def main():
    # 1. 初始化目录
    create_dirs()
    
    # 2. 检查 API Key
    if not DASHSCOPE_API_KEY:
        logger.error("❌ 请设置 DASHSCOPE_API_KEY 环境变量（在 .env 文件中配置）")
        return
    
    # 3. 下载文档
    downloader = DocumentDownloader()
    downloader.download_all_sources()
    
    # 4. 解析与清洗文档
    processor = DocumentProcessor()
    all_docs = processor.process_all_documents()
    
    if not all_docs:
        logger.error("❌ 未加载到任何有效文档")
        return
    
    # 5. 构建向量库
    build_vector_db(all_docs)
    
    logger.info("===== 全自动 Python 知识库构建完成 =====")
    logger.info(f"📁 原始文档路径: {RAW_DATA_PATH}")
    logger.info(f"📁 清洗后文档路径: {CLEAN_DATA_PATH}")
    logger.info(f"📁 向量库路径: {PERSIST_DIR}")
    logger.info(f"📄 日志文件路径: {LOG_DIR / 'build_kb.log'}")

if __name__ == "__main__":
    main()
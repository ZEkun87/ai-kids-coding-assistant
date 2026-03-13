# ai-kids-coding-assistant
AI 少儿编程助手项目


> 一个基于 FastAPI + DashScope + ChromaDB 的 AI 少儿编程辅导助手
> 适合小学生和初中生的 Python 编程学习与练习辅助工具。

---

## 功能概览

1. **问答辅助**

   * 根据用户提问，结合知识库文档，生成适合少儿理解的回答。

2. **代码分析**

   * 分析 Python 代码，指出语法或逻辑问题，并给出少儿易懂的修改建议。

3. **练习题生成**

   * 根据主题生成适合初学者的编程练习题。

4. **文件上传 / 知识库入库**

   * 支持 PDF、DOCX、TXT 文件上传，自动提取文本并生成向量存入 ChromaDB。

5. **历史记录**

   * 保存问答记录，可按分类查询最近的聊天历史。

6. **流式回答**

   * 支持问答流式返回，边生成边显示回答内容。

---

## 技术栈

* Python 3.10
* FastAPI（Web API 框架）
* DashScope（AI 问答与文本嵌入）
* ChromaDB（向量数据库，用于知识库检索）
* SQLAlchemy + SQLite（本地聊天记录存储）
* PyPDF2 / python-docx（文档解析）
* Docker（容器化部署，可选）

---

## 快速启动

### 1. 克隆仓库

```bash
git clone https://github.com/你的用户名/ai-kids-coding-assistant.git
cd ai-kids-coding-assistant
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
DASHSCOPE_API_KEY=你的_dashscope_api_key
```

> ⚠️ 切勿上传 `.env` 到 GitHub

### 3. 使用 Docker（推荐）

```bash
docker compose up -d --build backend
```

* 服务默认启动在 `http://localhost:8000`
* 查看日志：

```bash
docker compose logs -f backend
```

### 4. 直接本地运行（非 Docker）

```bash
# 建议在虚拟环境中运行
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 接口示例

### 根接口

```http
GET /
```

返回：

```json
{"message": "AI 少儿编程助手运行中"}
```

### 提问接口

```http
POST /ask
Content-Type: application/json

{
  "question": "如何在 Python 中打印数字？",
  "category": "python"
}
```

返回：

```json
{
  "answer": "你可以使用 print() 函数打印数字...",
  "request_id": "唯一请求ID",
  "sources": ["参考文档内容..."]
}
```

### 代码分析接口

```http
POST /analyze
Content-Type: application/json

{
  "code": "print('Hello World'"
}
```

返回：

```json
{
  "analysis": "你缺少一个右括号，可以改为 print('Hello World') ..."
}
```

### 练习题生成接口

```http
POST /exercise
Content-Type: application/json

{
  "topic": "循环"
}
```

返回：

```json
{
  "exercise": "请写一个程序，使用 for 循环打印 1-10 的数字..."
}
```

### 文件上传接口

```http
POST /upload?category=python
Content-Type: multipart/form-data
file=@example.pdf
```

返回：

```json
{
  "status": "success",
  "count": 3,
  "category": "python",
  "msg": "文档已成功入库 RAG 知识库"
}
```

### 聊天记录接口

```http
GET /history?category=python&limit=10
```

返回：

```json
[
  {
    "question": "如何打印数字？",
    "answer": "...",
    "category": "python",
    "date": "2026-03-12T12:34:56"
  }
]
```

---

## 项目结构示例

```
ai-coding-tutor/
├─ backend/
│  ├─ main.py           # 主服务入口
│  ├─ requirements.txt  # 依赖列表
│  └─ ...
├─ docker-compose.yml
├─ .env                 # 环境变量 (本地)
└─ README.md
```

---

## 注意事项

* `.env` 文件和数据库 (`vector_db/`, `chat_history.db`) **不要上传到 GitHub**。
* 如需重置知识库，可删除 `vector_db/` 目录，但确保服务未运行。

---

## License

MIT License（可根据需求修改）

---

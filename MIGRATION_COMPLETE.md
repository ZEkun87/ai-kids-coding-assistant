# PostgreSQL + PGVector 迁移完整说明

## 📦 本次提供的文件

### 1. **migrate_to_postgres.py** 
   - 自动化迁移脚本
   - 功能: 从SQLite迁移聊天历史，从Chroma迁移向量数据
   - 使用: `python3 migrate_to_postgres.py`

### 2. **validate_migration.py**
   - 迁移验证脚本
   - 功能: 完整性检查、性能基准测试
   - 使用: `python3 validate_migration.py`

### 3. **MIGRATION_GUIDE.md**
   - 详细迁移指南 (这个文件)
   - 包含: 前置条件、步骤说明、常见问题、性能对比

---

## 🚀 快速开始 (5分钟)

### 第1步: 安装PostgreSQL

```bash
# macOS
brew install postgresql@17
brew services start postgresql@17

# 验证
psql --version
```

### 第2步: 创建数据库和用户

```bash
# 创建用户
createuser -P ai_tutor_user  # 输入密码时设为: postgres

# 创建数据库
createdb -O ai_tutor_user ai_coding_tutor_prod
```

### 第3步: 配置环境变量

编辑 `.env` 或 `.env.production`:

```bash
DATABASE_URL=postgresql+psycopg://ai_tutor_user:postgres@localhost:5432/ai_coding_tutor_prod
DASHSCOPE_API_KEY=sk_xxxxxxxxxxxx
```

### 第4步: 初始化数据库

```bash
cd backend
python3 << 'EOF'
import os
from models.chat import engine, Base

# 创建所有表
Base.metadata.create_all(engine)
print("✅ 数据库初始化完成")
EOF
```

### 第5步: 执行迁移

```bash
cd /Users/yuzekun/ai-coding-tutor
python3 migrate_to_postgres.py
```

### 第6步: 验证迁移

```bash
python3 validate_migration.py
```

---

## ⚙️ 核心配置原理

### SQLAlchemy 数据库连接

在 `backend/models/chat.py` 中配置:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 从环境变量读取
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://user:password@localhost:5432/db_name"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,  # 设为True可以看到SQL语句
    pool_size=10,  # 连接池大小
    max_overflow=20  # 溢出连接数
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### 数据模型

```python
# 聊天记录表
class ChatRecord(Base):
    __tablename__ = "chat_records"
    id: Column(Integer, primary_key=True)
    question: str  # 用户问题
    answer: str    # 模型回答
    category: str  # 分类标签
    date: datetime # 时间戳

# 文档块表 (向量存储)
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Column(Integer, primary_key=True)
    content: str   # 文档内容
    source: str    # 来源
    category: str  # 分类
    created_at: datetime

# 向量嵌入表
class Embedding(Base):
    __tablename__ = "embeddings"
    id: Column(Integer, primary_key=True)
    document_id: int  # 对应的文档
    embedding: Vector(1024)  # 1024维向量
    model: str  # 使用的模型
```

---

## 📊 数据库架构对比

### 旧架构 (SQLite + Chroma)
```
┌─────────────────────────────────────┐
│  应用程序                            │
├──────────────┬──────────────────────┤
│ SQLite DB    │  Chroma (向量DB)    │
│ (聊天历史)    │  (向量存储)         │
├──────────────┼──────────────────────┤
│ • cat.db     │ • cdef/metadata.json │
│ • history    │ • cdef/data.parquet  │
│ • single-file│ • separate process   │
└──────────────┴──────────────────────┘
```

### 新架构 (PostgreSQL + PGVector)
```
┌─────────────────────────────────────┐
│  应用程序                            │
├─────────────────────────────────────┤
│  PostgreSQL + PGVector              │
│  ┌─────────────────────────────┐   │
│  │ chat_records (聊天历史)      │   │
│  │ document_chunks (文档)       │   │
│  │ embeddings (向量，含索引)     │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 🔍 迁移脚本工作流

### migrate_to_postgres.py 工作流程:

```
1. 检查PostgreSQL连接
   └─ 失败? → 显示错误并退出

2. 迁移聊天历史
   ├─ 读取 chat_history.db
   ├─ 遍历每条记录
   ├─ 插入到 PostgreSQL
   └─ 返回迁移数量

3. 迁移向量存储
   ├─ 读取 chroma_db/
   ├─ 连接到DashScope API (计算缺失的向量)
   ├─ 将所有向量插入到 embeddings 表
   └─ 返回迁移数量

4. 生成迁移报告
   └─ 显示总数和详细统计
```

### 关键错误处理:

```python
# 1. 连接失败
if not postgres_connection:
    log.error("PostgreSQL连接失败: 检查.env和数据库服务")
    
# 2. 特定记录失败
for record in records:
    try:
        migrate(record)
    except Exception as e:
        log.warning(f"记录 {record.id} 失败，继续处理其他")
        continue

# 3. 如果向量计算失败
if no_embedding:
    embedding = dashscope.embed(content)
    insert_embedding(embedding)
```

---

## ✅ 验证脚本检查项

### validate_migration.py 执行的检查:

| 检查项 | 通过条件 | 失败影响 |
|--------|---------|---------|
| PostgreSQL连接 | 能连接 | 无法进行任何操作 |
| 数据库表存在 | 全部表都存在 | 表未创建 |
| PGVector扩展 | 已安装 | 向量搜索不可用 |
| 聊天记录数 | 新=旧 | 数据丢失 |
| 向量文档数 | 新≥旧×0.9 | 部分向量未迁移（500个文档） |
| 查询性能 | <100ms | 性能不佳 |

---

## 🔧 常见故障排除

### 问题1: `ERROR: connection refused`

**原因**: PostgreSQL服务未启动

**解决**:
```bash
# 启动PostgreSQL
brew services start postgresql@17

# 验证状态
brew services list | grep postgres

# 手动启动（调试用）
pg_ctl -D /opt/homebrew/var/postgres start
```

### 问题2: `ERROR: FATAL: Ident authentication failed`

**原因**: 认证配置错误

**解决**:
```bash
# 编辑认证配置
nano /opt/homebrew/var/postgres/pg_hba.conf

# 修改本地连接为trust（开发环境）
# local   all             all                                     trust

# 重启PostgreSQL
brew services restart postgresql@17
```

### 问题3: 迁移后向量搜索不工作

**原因**: PGVector扩展未安装或向量维度不匹配

**解决**:
```bash
# 安装PGVector扩展
psql ai_coding_tutor_prod << 'EOF'
CREATE EXTENSION IF NOT EXISTS vector;
SHOW vector.libversion;
EOF

# 验证向量表
psql ai_coding_tutor_prod -c "SELECT COUNT(*) FROM embeddings;"
```

### 问题4: 性能缓慢

**原因**: 缺少索引或配置不优

**解决**:
```sql
-- 添加索引
CREATE INDEX idx_chat_records_category ON chat_records(category);
CREATE INDEX idx_embeddings_model ON embeddings(model);

-- 向量搜索索引 (使用HNSW)
CREATE INDEX idx_embeddings_vector ON embeddings USING hnsw (embedding vector_cosine_ops);

-- 分析查询计划
EXPLAIN ANALYZE
SELECT * FROM chat_records WHERE category = 'python' LIMIT 10;
```

---

## 📈 性能优化建议

### PostgreSQL 配置优化 (`postgresql.conf`)

```ini
# 内存配置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 64MB

# 连接配置
max_connections = 200
max_prepared_transactions = 100

# 向量搜索优化
search_path = 'public, pgvector'

# 日志配置
log_min_duration_statement = 1000  # 记录>1s的查询
```

### 数据库维护

```bash
# 清理不用的数据
VACUUM ANALYZE;

# 重建索引
REINDEX INDEX ALL;

# 导出统计信息
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🔐 备份和恢复

### 自动备份策略

```bash
#!/bin/bash
# backup_postgres.sh - 每日备份脚本

BACKUP_DIR="$HOME/postgres_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="ai_coding_tutor_prod"

mkdir -p "$BACKUP_DIR"

# 完整备份
pg_dump "$DB_NAME" | gzip > "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# 保留最近7天的备份
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
```

### 恢复流程

```bash
# 从备份恢复
gunzip < ~/postgres_backups/backup_20250101_120000.sql.gz | \
  psql ai_coding_tutor_prod

# 验证恢复
psql ai_coding_tutor_prod -c "SELECT COUNT(*) FROM chat_records;"
```

---

## 🚀 迁移后验证清单

- [ ] ✅ PostgreSQL 服务运行正常
- [ ] ✅ 数据库连接成功
- [ ] ✅ 所有表已创建
- [ ] ✅ 聊天记录已迁移 (数量一致)
- [ ] ✅ 向量数据已迁移 (数量相近)
- [ ] ✅ 查询性能正常 (<100ms)
- [ ] ✅ PGVector 扩展可用
- [ ] ✅ API 接口功能正常
- [ ] ✅ 备份策略已部署
- [ ] ✅ 监控告警已配置 (可选)

---

## 📞 支持和故障排除

### 获取详细的日志

```python
# 启用SQLAlchemy SQL日志
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# 启用psycopg日志
import psycopg
logging.getLogger('psycopg').setLevel(logging.DEBUG)
```

### 检查系统资源

```bash
# 查看PostgreSQL进程
ps aux | grep postgres

# 查看端口占用
lsof -i :5432

# 查看共享内存使用
ipcs -m
```

### 获取帮助

- **PostgreSQL 文档**: https://www.postgresql.org/docs/latest/
- **PGVector GitHub**: https://github.com/pgvector/pgvector
- **SQLAlchemy 文档**: https://docs.sqlalchemy.org/
- **项目问题追踪**: [GitHub Issues]

---

## 📝 许可证

本迁移脚本随项目一起提供，遵循相同的许可证。

---

**最后更新**: 2026年4月
**版本**: 1.0.0
**状态**: 生产就绪 ✅

# 从SQLite+Chroma迁移到PostgreSQL+PGVector

## 📋 概述

本指南介绍如何将您的应用数据从SQLite + Chroma迁移到PostgreSQL + PGVector。

### 为什么迁移？

| 方面 | SQLite + Chroma | PostgreSQL + PGVector |
|------|-----------------|----------------------|
| **扩展性** | 单文件，不适合大规模 | 企业级，支持大数据量 |
| **向量查询** | 需要单独的Chroma | 原生pgvector扩展 |
| **并发性** | 有限 | 优秀 |
| **数据安全** | 基础 | 备份、复制、高可用 |
| **查询性能** | 小规模可以，大规模卡顿 | 优化的HNSW索引 |

---

## 🚀 快速迁移

### 1. 前置条件

```bash
# 安装PostgreSQL (macOS)
brew install postgresql@17

# 启动PostgreSQL服务
brew services start postgresql@17

# 验证安装
psql --version
```

### 2. 创建迁移数据库

```bash
# 创建新数据库
createdb ai_coding_tutor_prod

# 验证
psql -l | grep ai_coding_tutor
```

### 3. 配置环境变量

更新 `.env` 或 `.env.production`:

```bash
# 数据库配置
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/ai_coding_tutor_prod

# DashScope API （用于向量嵌入）
DASHSCOPE_API_KEY=sk_xxxxxxxxxxxx
```

### 4. 初始化新数据库

```bash
cd backend
python3 -c "
from models.chat import engine, Base
Base.metadata.create_all(engine)
"
```

### 5. 运行迁移脚本

```bash
# 从项目根目录运行
python3 migrate_to_postgres.py
```

**预期输出：**
```
==================================================
🚀 从SQLite+Chroma迁移到PostgreSQL+PGVector
==================================================
✅ PostgreSQL连接成功
🔄 开始迁移聊天历史...
📋 找到 150 条旧记录
✅ 成功迁移 150 条聊天记录
🔄 开始迁移向量存储...
✅ 成功迁移 2500 个向量文档
==================================================
📊 迁移摘要:
  • 聊天历史: 150 条记录
  • 向量文档: 2500 个文档
==================================================
✅ 迁移完成!
```

---

## 📊 详细步骤

### 步骤1: 安装依赖

```bash
cd backend

# 更新requirements.txt时确保包含：
pip install psycopg[binary]  # PostgreSQL驱动
pip install pgvector         # PGVector Python客户端

# 或直接安装
pip install -r requirements.txt
```

### 步骤2: 验证旧数据

```bash
# 查看旧SQLite数据库
sqlite3 backend/chat_history.db ".tables"
sqlite3 backend/chat_history.db "SELECT COUNT(*) FROM chat_records;"

# 查看Chroma集合
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='backend/chroma_db')
for col in client.list_collections():
    print(f'{col.name}: {col.count()} 条文档')
"
```

### 步骤3: 执行迁移

```bash
# 详细日志输出
python3 migrate_to_postgres.py -v

# 仅回滚测试（不修改数据）
python3 migrate_to_postgres.py --dry-run
```

### 步骤4: 验证迁移

```bash
# 连接到新数据库
psql ai_coding_tutor_prod

# 验证表存在
\dt  # 列出所有表

# 验证数据
SELECT COUNT(*) FROM chat_records;
SELECT COUNT(*) FROM document_chunks;
SELECT COUNT(*) FROM embeddings;
```

### 步骤5: 更新应用配置

```bash
# 编辑 .env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/ai_coding_tutor_prod

# 重启应用
docker-compose -f compose.yaml up --build
```

---

## 🔍 常见问题

### Q1: 迁移失败，如何回滚？

```bash
# 删除新数据库
dropdb ai_coding_tutor_prod

# 旧数据仍然安全
ls -la backend/chat_history.db
ls -la backend/chroma_db/
```

### Q2: 如何检查迁移进度？

```bash
# 实时监控
watch -n 5 "psql ai_coding_tutor_prod -c 'SELECT COUNT(*) FROM chat_records;'"
```

### Q3: 向量迁移后能否删除Chroma？

```bash
# 验证所有向量已迁移
psql ai_coding_tutor_prod -c "SELECT COUNT(*) FROM embeddings;"

# 确认数字与原Chroma相同后，可以安全删除
rm -rf backend/chroma_db/
```

### Q4: PostgreSQL性能调优？

编辑 `/opt/homebrew/var/postgres/postgresql.conf`:

```sql
-- 向量搜索优化
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB

-- PGVector配置
maintenance_work_mem = 64MB
```

然后重启：
```bash
brew services restart postgresql@17
```

---

## 📈 性能对比

### 查询性能测试

```sql
-- SQLite (现有)
SELECT * FROM chat_records WHERE category = 'python' LIMIT 100;
-- 通常: 5-50ms

-- PostgreSQL (迁移后)  
SELECT * FROM chat_records WHERE category = 'python' LIMIT 100;
-- 通常: 1-5ms

-- 向量相似性搜索（新能力）
SELECT id, content, similarity FROM document_chunks 
WHERE embedding <=> $1::vector(1024) < 0.3
LIMIT 50;
-- 使用HNSW索引: < 10ms
```

---

## 🔒 备份和灾难恢复

### 自动备份（PG）

```bash
# 创建备份目录
mkdir -p ~/postgres_backups

# 自动备份脚本
cat > ~/postgres_backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/postgres_backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump ai_coding_tutor_prod | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"
echo "Backup created: backup_$DATE.sql.gz"
EOF

chmod +x ~/postgres_backup.sh

# 添加到crontab（每天凌晨2点备份）
crontab -e
# 添加: 0 2 * * * ~/postgres_backup.sh
```

### 恢复备份

```bash
# 恢复数据库
gunzip < ~/postgres_backups/backup_20250101_020000.sql.gz | psql ai_coding_tutor_prod
```

---

## ✅ 迁移检查清单

- [ ] PostgreSQL已安装并运行
- [ ] 新数据库已创建
- [ ] `.env` 已更新DATABASE_URL
- [ ] DASHSCOPE_API_KEY已设置
- [ ] 依赖已安装 (`psycopg`, `pgvector`)
- [ ] 旧数据已备份 (`sqlite3` + `chroma_db`)
- [ ] 迁移脚本执行成功
- [ ] 数据验证通过（行数一致）
- [ ] 应用程序测试通过
- [ ] 性能基准测试完成
- [ ] 生产环境已准备

---

## 🚨 注意事项

1. **备份旧数据** — 迁移前保存完整备份
2. **测试环境优先** — 先在开发环境验证
3. **性能测试** — 确保查询性能满足要求
4. **API兼容性** — 应用代码无需改动
5. **计划停机** — 迁移期间应用可离线

---

## 📞 故障排除

### 连接错误

```
Error: connection refused
```

**解决：**
```bash
# 检查PostgreSQL状态
brew services list | grep postgres

# 重启服务
brew services restart postgresql@17

# 检查监听端口
netstat -an | grep 5432 || sudo netstat -an | grep 5432
```

### 权限错误

```
Error: FATAL: Ident authentication failed
```

**解决：**
```bash
# 编辑pg_hba.conf
export PG_CONF=$(psql -U postgres -t -c "SHOW config_file")
nano $PG_CONF

# 修改authentication方法为md5或trust（开发环境）
# local   all             all                                     trust
brew services restart postgresql@17
```

### 导入错误

```
Error: UNIQUE constraint failed
```

**解决：**
```bash
# 清空目标表
psql ai_coding_tutor_prod -c "TRUNCATE chat_records CASCADE;"

# 重新迁移
python3 migrate_to_postgres.py
```

---

## 🎓 相关文档

- [PostgreSQL官方文档](https://www.postgresql.org/docs/)
- [PGVector GitHub](https://github.com/pgvector/pgvector)
- [DashScope文档](https://help.aliyun.com/zh/dashscope/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/)

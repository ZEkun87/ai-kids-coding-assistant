# API密钥安全管理指南

## ⚠️ 当前密钥状态

**你的当前API密钥已在Git历史记录中暴露！**

密钥: `sk-e1240d5855d14fceba75c2326158c1c3`

即使已经从 `.gitignore` 中忽略，这个密钥也可能在以下地方被看到：
- Git提交历史中
- 备份中
- 其他人的本地克隆中

---

## 🔐 立即采取的安全步骤

### 步骤 1: 撤销旧密钥（**立即执行**）

1. 访问 [DashScope 控制台](https://dashscope.console.aliyun.com)
2. 登录you的账户
3. 进入 "API密钥管理" 或类似section
4. 找到并删除密钥: `sk-e1240d5855d14fceba75c2326158c1c3`
5. **确认删除** - 旧密钥将立即失效

### 步骤 2: 生成新密钥

1. 在DashScope控制台中创建新的API密钥
2. 复制新密钥（只会显示一次！）
3. 保存到本地安全的地方（例如密码管理器）

### 步骤 3: 更新.env文件

编辑 `.env` 文件，替换为新密钥：

```bash
# 使用编辑器打开.env
nano .env
# 或
vim .env
```

将内容改为：
```
DASHSCOPE_API_KEY=你的新密钥（例如：sk-xxxx...）
```

---

## 🛡️ 环境变量最佳实践

### 开发环境

**`.env.local` (个人本地用，不提交)**
```bash
# 复制.env.example为.env.local再编辑
cp .env.example .env.local
# 编辑和添加你的本地密钥
nano .env.local
```

### 测试环境

**`.env.test`**
```bash
DASHSCOPE_API_KEY=test_key_for_testing
ENVIRONMENT=test
```

### 生产环境

**使用环境变量或密钥管理服务，不要在文件中存储！**

选项A: 系统环境变量
```bash
export DASHSCOPE_API_KEY="your_production_key"
python -m uvicorn main:app
```

选项B: Docker/Kubernetes密钥
```yaml
# docker-compose.yaml
services:
  backend:
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
```

```bash
# 启动时：
DASHSCOPE_API_KEY="your_production_key" docker-compose up
```

选项C: CI/CD密钥管理
- GitHub Secrets
- GitLab CI Variables
- Jenkins Credentials

---

## 📝 改进的.env.local.example模板

这是用于本地开发的安全模板：

```bash
# ============================================
# 本地开发配置 (.env.local)
# ============================================
# 复制此文件为 .env.local 并填入你的值
# .env.local 不要提交到Git！已在.gitignore中

# DashScope API (从 https://dashscope.console.aliyun.com 获取)
DASHSCOPE_API_KEY=your_local_development_key_here

# 向量数据库路径
PERSIST_DIR=./backend/vector_db

# Python环境
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# 开发环境标志
DEBUG=true
ENV=development
```

---

## 🔄 密钥轮换流程

### 定期轮换密钥（建议每3-6个月）

1. **生成新密钥** (DashScope控制台)
2. **临时保存两个密钥** (新旧)
3. **更新应用配置** 使用新密钥
4. **测试应用** 确认新密钥工作
5. **删除旧密钥** (DashScope控制台)

### 紧急轮换（密钥泄露时）

1. **立即删除旧密钥** (DashScope控制台禁用)
2. **生成新密钥** (立即)
3. **更新所有环境** (.env, Docker, CI/CD等)
4. **通知团队成员** 已更换密钥
5. **检查日志** 看是否有异常调用

---

## 🐳 Docker/Docker-Compose安全配置

### 安全的compose.yaml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ai-coding-tutor-backend
    restart: always
    ports:
      - "8000:8000"
    # ✅ 使用环境变量，不要硬编码密钥
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - PYTHONUNBUFFERED=1
      - PERSIST_DIR=/app/vector_db
    volumes:
      - ./backend/vector_db:/app/vector_db
      - ./data:/app/data
    networks:
      - coding-tutor-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  coding-tutor-network:
    driver: bridge
```

### 启动方式（安全）

```bash
# ✅ 良好做法：从外部传入密钥
DASHSCOPE_API_KEY=$(cat ~/.dashscope_key) docker-compose up

# 或从.env.local加载
set -a
source .env.local
set +a
docker-compose up
```

### 不安全的做法（❌ 避免）

```bash
# ❌ 不要硬编码在compose.yaml中
# ❌ 不要在命令行历史中输入明文密钥
# ❌ 不要提交含有真实密钥的文件
```

---

## 🔒 更高级的安全措施

### 1. 使用AWS Secrets Manager 或 HashiCorp Vault

```python
# 从AWS Secrets Manager读取密钥
import boto3

def get_dashscope_key():
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId='dashscope_api_key')
    return secret['SecretString']
```

### 2. 使用.env加密

```bash
# 使用python-dotenv-vault
pip install python-dotenv-vault

# 创建加密的.env文件
dotenv-vault-core encrypt
```

### 3. GitHub Actions CI/CD安全配置

```yaml
# .github/workflows/deploy.yml
name: Deploy
on: push

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        env:
          DASHSCOPE_API_KEY: ${{ secrets.DASHSCOPE_API_KEY }}
        run: |
          docker-compose up -d
```

---

## 📋 检查清单

立即完成以下操作：

- [ ] **撤销旧密钥** - DashScope控制台删除 `sk-e1240d5855d14fceba75c2326158c1c3`
- [ ] **生成新密钥** - DashScope控制台创建新密钥
- [ ] **更新.env** - 替换为新密钥
- [ ] **测试应用** - 确认新密钥有效
  ```bash
  python -m pytest  # 运行测试
  curl http://localhost:8000/  # 测试API
  ```
- [ ] **验证.gitignore** - 确保.env在忽略列表中
  ```bash
  git check-ignore .env  # 应该返回 ".env"
  ```
- [ ] **创建.env.local** - 本地开发用
- [ ] **通知团队** - 密钥已更换

---

## 🚀 推荐流程

### 对于新项目或已有团队的项目

1. **使用.env.template或.env.example** ✅ (已设置)
2. **.env放在.gitignore** ✅ (已设置)
3. **本地开发使用.env.local** (需创建)
4. **CI/CD使用环境变量** (需配置)
5. **生产环境使用密钥管理服务** (需部署时配置)

### 本地开发流程

```bash
# 1. 克隆项目
git clone <repo>
cd ai-coding-tutor

# 2. 复制模板
cp .env.example .env.local

# 3. 编辑本地配置
nano .env.local
# 添加你的DASHSCOPE_API_KEY

# 4. 验证.env.local不会被提交
git check-ignore .env.local  # 应该返回 ".env.local"
# 如果没有显示，添加到.gitignore

# 5. 启动应用
source .env.local
python -m uvicorn backend.main:app --reload
```

---

## 🔐 长期安全建议

1. **每季度轮换密钥** - 即使没有泄露迹象
2. **使用密钥管理工具** - 不要在文件中存储密钥
3. **审计密钥使用** - 定期检查API使用日志
4. **限制密钥权限** - 如果DashScope支持，限制密钥访问范围
5. **团队培训** - 确保所有开发者了解密钥安全
6. **自动化检测** - 使用工具检测误提交的密钥
   ```bash
   # 安装git-secrets防止密钥提交
   brew install git-secrets
   git secrets --install
   git secrets --register-aws  # 或定制规则
   ```

---

## ✅ 安全检验

完成上述步骤后，运行以下检查：

```bash
# 1. 检查.env是否在.gitignore中
grep "\.env" .gitignore

# 2. 验证历史记录中是否有密钥
git log --all --full-history --source --remotes -S "sk-" 
# 如果找到，需要使用 git-filter-branch 或 BFG Repo-Cleaner 清理

# 3. 检查是否有泄露的密钥
git diff HEAD~20 HEAD | grep -i "api.*key"

# 4. 验证当前.env不会被提交
git status | grep ".env"  # 应该不显示
```

---

**现在就开始保护你的API密钥！** 🔐


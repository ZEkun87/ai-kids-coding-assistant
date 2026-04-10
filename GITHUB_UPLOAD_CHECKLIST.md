# 📤 GitHub 上传检查清单 | GitHub Upload Checklist

在将项目上传到 GitHub 之前，请完成以下检查以确保安全性和完整性。

---

## ✅ 必做事项 | Must-Do Items

### 1. 敏感信息清理

```bash
# 检查是否有硬编码的 API Key
grep -r "sk-" . --include="*.py" --include="*.js" --include="*.jsx"
grep -r "API_KEY" . --include="*.py" --include="*.js" --include="*.jsx"

# 检查 .env 文件是否被忽略
cat .gitignore | grep ".env"

# 确保没有提交数据库文件
ls -la *.db vector_db/ chroma_db/ 2>/dev/null
```

**预期结果**: 
- ❌ 不应找到任何真实的 API Key
- ✅ `.env` 应在 `.gitignore` 中
- ✅ 数据库文件不应被跟踪

---

### 2. 许可证文件确认

```bash
# 检查 LICENSE 文件是否存在
ls -l LICENSE

# 查看许可证内容
head -20 LICENSE
```

**必须包含**:
- ✅ 非商业使用声明
- ✅ 版权声明
- ✅ 禁止行为列表
- ✅ 联系方式

---

### 3. README 完整性

```bash
# 检查 README 是否存在
ls -l README.md

# 验证关键章节
grep -E "^## " README.md
```

**应包含的章节**:
- ✅ 项目简介
- ✅ 核心特性
- ✅ 快速开始
- ✅ API 文档
- ✅ 许可证声明
- ⚠️ 重要声明（非商业用途）

---

### 4. 水印验证

```bash
# 检查 main.py 中的水印
grep -A 5 "PROJECT_METADATA" backend/main.py

# 验证 API 响应头中间件
grep -A 5 "add_copyright_header" backend/main.py

# 检查启动日志水印
grep "Watermark" backend/main.py
```

**应看到**:
- ✅ `KIDS_CODING_TUTOR_2024_AUTHORIZED`
- ✅ 作者信息
- ✅ 版权声明

---

### 5. GitHub 配置文件

```bash
# 检查 .github 目录
ls -la .github/

# 应包含的文件
ls .github/SECURITY.md
ls .github/CONTRIBUTING.md
```

**必须存在**:
- ✅ `.github/SECURITY.md` - 安全策略
- ✅ `.github/CONTRIBUTING.md` - 贡献指南

---

### 6. .gitignore 完整性

```bash
# 检查关键忽略项
cat .gitignore | grep -E "\.env|\.db|node_modules|__pycache__"
```

**应忽略**:
- ✅ `.env`, `.env.local`
- ✅ `*.db`, `vector_db/`, `chroma_db/`
- ✅ `node_modules/`
- ✅ `__pycache__/`
- ✅ `.venv/`, `venv/`

---

### 7. 依赖文件检查

```bash
# 后端依赖
cat backend/requirements.txt

# 前端依赖
cat frontend/vite-project/package.json | grep -A 10 '"dependencies"'
```

**确保**:
- ✅ 没有硬编码的版本号问题
- ✅ 所有依赖都是公开可用的

---

### 8. Docker 配置

```bash
# 检查 Docker 文件
ls -l compose.yaml
ls -l backend/Dockerfile
ls -l frontend/vite-project/Dockerfile

# 验证环境变量引用
grep -E "\$\{|DB_|DASHSCOPE" compose.yaml
```

**应使用环境变量**:
- ✅ `${DASHSCOPE_API_KEY}`
- ✅ `${DB_PASSWORD}`
- ✅ 不应有硬编码的密钥

---

## 🔍 安全检查 | Security Check

### 运行安全检查脚本

```bash
# 如果项目中有安全检查脚本
chmod +x check_api_key_security.sh
./check_api_key_security.sh
```

### 手动检查常见泄露点

```bash
# 1. 检查 Python 文件
find . -name "*.py" -exec grep -l "password\|secret\|key" {} \;

# 2. 检查配置文件
find . -name "*.yaml" -o -name "*.yml" -o -name "*.json" | xargs grep -l "password\|secret" 2>/dev/null

# 3. 检查 JavaScript 文件
find . -name "*.js" -o -name "*.jsx" | xargs grep -l "API.*KEY\|SECRET" 2>/dev/null

# 4. 检查历史提交（如果有 git 历史）
git log --all --full-history --source -- "*password*" "*secret*" "*api_key*" 2>/dev/null
```

**注意**: 如果发现敏感信息，立即：
1. 从 git 历史中移除
2. 更换泄露的密钥
3. 重新提交

---

## 📝 文档完整性 | Documentation

### 必需文档

```bash
# 检查所有必需文档
ls -l README.md
ls -l LICENSE
ls -l PROTECTION_GUIDE.md
ls -l .github/SECURITY.md
ls -l .github/CONTRIBUTING.md
ls -l .env.example
```

### 可选但推荐的文档

```bash
# 检查额外文档
ls -l CHANGELOG.md        # 更新日志
ls -l CODE_OF_CONDUCT.md  # 行为准则
ls -l INSTALL.md          # 详细安装指南
```

---

## 🧪 功能测试 | Functionality Test

### 本地测试

```bash
# 1. 后端启动测试
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000 &

# 2. 测试 API
curl http://localhost:8000/
# 应返回包含水印信息的 JSON

# 3. 检查响应头
curl -I http://localhost:8000/
# 应看到 X-Watermark-ID, X-Copyright 等头部

# 4. 停止服务
kill %1
```

### Docker 测试

```bash
# 构建并启动
docker-compose up -d --build

# 检查容器状态
docker-compose ps

# 测试服务
curl http://localhost:8000/
curl http://localhost:3000/

# 查看日志
docker-compose logs backend
docker-compose logs frontend

# 停止
docker-compose down
```

---

## 🎯 最终检查清单 | Final Checklist

在点击 "Push to GitHub" 之前，确认以下所有项：

### 代码层面
- [ ] 无硬编码的 API Key 或密码
- [ ] 所有敏感信息使用环境变量
- [ ] 水印标识存在于关键文件中
- [ ] 代码注释包含版权声明
- [ ] 无调试代码或临时文件

### 文档层面
- [ ] README.md 完整且最新
- [ ] LICENSE 文件存在且正确
- [ ] PROTECTION_GUIDE.md 存在
- [ ] .github/SECURITY.md 存在
- [ ] .github/CONTRIBUTING.md 存在
- [ ] .env.example 提供配置模板

### 配置层面
- [ ] .gitignore 正确配置
- [ ] Docker 配置使用环境变量
- [ ] 无 .env 或其他敏感文件被跟踪
- [ ] 数据库文件未被跟踪

### 法律层面
- [ ] 明确标注非商业用途
- [ ] 包含商业授权联系方式
- [ ] 版权声明清晰可见
- [ ] 侵权追责说明明确

### 功能层面
- [ ] 本地可以正常启动
- [ ] Docker 可以正常构建
- [ ] API 响应包含水印信息
- [ ] 前端可以正常访问

---

## 🚀 上传步骤 | Upload Steps

### 首次上传

```bash
# 1. 初始化 Git 仓库（如果还没有）
git init

# 2. 添加所有文件
git add .

# 3. 提交
git commit -m "Initial commit: AI Kids Coding Assistant v1.0.0

- Complete RAG + Multi-Agent architecture
- Non-commercial use license with watermark protection
- Full documentation and security measures
- Docker support for easy deployment"

# 4. 关联远程仓库
git remote add origin https://github.com/your-username/ai-kids-coding-assistant.git

# 5. 推送到 GitHub
git branch -M main
git push -u origin main
```

### 更新已有仓库

```bash
# 1. 检查更改
git status

# 2. 添加更改
git add .

# 3. 提交
git commit -m "Update: Add protection mechanisms and optimize README

- Add digital watermark system
- Update LICENSE to non-commercial use
- Add SECURITY.md and CONTRIBUTING.md
- Optimize README for GitHub"

# 4. 推送
git push origin main
```

---

## ⚠️ 上传后验证 | Post-Upload Verification

### 1. 检查 GitHub 仓库

访问: `https://github.com/your-username/ai-kids-coding-assistant`

确认:
- [ ] README 正确渲染
- [ ] LICENSE 被 GitHub 识别
- [ ] 所有文件都存在
- [ ] 无敏感信息泄露

### 2. 测试克隆

```bash
# 在新目录测试克隆
cd /tmp
git clone https://github.com/your-username/ai-kids-coding-assistant.git
cd ai-kids-coding-assistant

# 验证文件完整性
ls -l README.md LICENSE PROTECTION_GUIDE.md
ls -la .github/

# 尝试启动（需要配置 .env）
cp .env.example .env
# 编辑 .env 填入测试用的 API Key
```

### 3. 监控设置

在 GitHub 仓库设置中：
- [ ] 启用 Issues
- [ ] 启用 Discussions（可选）
- [ ] 设置 Branch Protection Rules
- [ ] 添加 Topics 标签
- [ ] 设置 Website URL（如果有）

---

## 🔔 持续维护 | Ongoing Maintenance

### 定期任务

**每周**:
- [ ] 检查 Issues 和 Pull Requests
- [ ] 回复用户问题

**每月**:
- [ ] 搜索是否有侵权副本
- [ ] 更新依赖版本
- [ ] 检查安全漏洞

**每季度**:
- [ ] 更新文档
- [ ] 评估是否需要更新水印 ID
- [ ] 审查许可证条款

---

## 📞 需要帮助？

如果在上传过程中遇到问题：

1. 查看 [PROTECTION_GUIDE.md](PROTECTION_GUIDE.md)
2. 查看 [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md)
3. 联系: zekunio@outlook.com

---

<div align="center">

**祝上传顺利！Good luck with your upload!**

🔒 记得保护你的知识产权 | Remember to protect your intellectual property

</div>

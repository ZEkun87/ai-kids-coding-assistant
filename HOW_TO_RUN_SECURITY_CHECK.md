# 🔍 check_api_key_security.sh 运行指南

## ⚡ 最简单的方式（一行命令）

```bash
bash check_api_key_security.sh
```

就这样！脚本会自动检查并显示结果。

---

## 📋 详细运行步骤

### 步骤1: 打开终端
- 打开 Terminal 或 iTerm
- 进入项目目录：
```bash
cd /Users/yuzekun/ai-coding-tutor
```

### 步骤2: 运行脚本
有多种方式可以运行：

**方式A: 最简单（推荐）**
```bash
bash check_api_key_security.sh
```

**方式B: 直接执行**
```bash
./check_api_key_security.sh
```

**方式C: 保存输出到文件**
```bash
bash check_api_key_security.sh > security_report.txt
```

**方式D: 同时查看和保存**
```bash
bash check_api_key_security.sh | tee security_report.txt
```

---

## 📊 脚本会检查什么？

脚本会自动进行5个安全检查：

| 检查项 | 说明 |
|--------|------|
| **检查1** | ✓ .env是否在.gitignore中 |
| **检查2** | ⚠️ Git历史中是否有泄露的密钥 |
| **检查3** | ⚠️ 当前文件中是否有硬编码密钥 |
| **检查4** | ✓ .env文件是否被提交过 |
| **检查5** | 📊 安全状态总结 |

---

## 🎯 完整运行示例

```bash
# 进入项目目录
cd /Users/yuzekun/ai-coding-tutor

# 运行安全检查
bash check_api_key_security.sh

# 输出示例：
# 🔍 API密钥安全检查工具
# =======================
# 
# [检查1] 验证.env是否在.gitignore中...
# ✓ .env 已正确配置在.gitignore中
# 
# [检查2] 扫描Git历史中的API密钥模式...
# ⚠️  发现可能的密钥泄露（DashScope格式）:
# 5c5ac5e Refactor backend...
# ...
```

---

## 📈 理解输出结果

### 输出中的符号

| 符号 | 含义 |
|------|------|
| ✓ | 安全无问题 |
| ⚠️ | 需要注意的问题（可能需要处理）|
| ✗ | 错误（必须处理）|
| ✅ | 好的做法 |
| ❌ | 不安全的做法 |

---

## 🔍 检查结果解读

### 检查1: .gitignore配置
```
✓ .env 已正确配置在.gitignore中
```
✅ 这很好，说明.env文件不会被提交到Git

### 检查2: Git历史泄露
```
⚠️  发现可能的密钥泄露（DashScope格式）:
5c5ac5e Refactor backend...
```
⚠️ 这是正常的，说明历史中有密钥（但已经被撤销了）
- 如果想清理，查看 CLEAN_GIT_HISTORY.md

### 检查3: 硬编码密钥
```
⚠️  发现硬编码的DASHSCOPE_API_KEY配置:
./backend/llm/dashscope_client.py:  api_key = os.getenv("DASHSCOPE_API_KEY")
```
✅ 这是好的做法！使用了 `os.getenv()` 从环境变量读取
❌ 坏做法：`DASHSCOPE_API_KEY="sk-xxxxx"` 直接赋值

### 检查4: .env提交历史
```
✓ .env文件未被提交到历史
```
✅ 完美，.env从未被提交到Git

### 检查5: 安全状态总结
```
✅ 好的做法:
  • 使用.env.local用于本地开发
  • 所有.env*文件在.gitignore中
  • 使用环境变量进行配置
```

---

## 🚀 定期运行建议

### 日常开发
```bash
# 每周运行一次检查
bash check_api_key_security.sh
```

### 密钥轮换后
```bash
# 更新密钥后立即运行
python api_key_manager.py rotate
bash check_api_key_security.sh  # 验证
```

### CI/CD中自动运行
```bash
# 在GitHub Actions中加入
- name: Check API Key Security
  run: bash check_api_key_security.sh
```

---

## 🆘 遇到错误怎么办？

### 错误1: "Permission denied"
```bash
# 解决方案：给脚本执行权限
chmod +x check_api_key_security.sh

# 然后运行
bash check_api_key_security.sh
```

### 错误2: "找不到文件"
```bash
# 确保你在正确的目录
pwd  # 应该显示 /Users/yuzekun/ai-coding-tutor

# 或使用完整路径
bash /Users/yuzekun/ai-coding-tutor/check_api_key_security.sh
```

### 错误3: "git: command not found"
```bash
# 安装Git（macOS用Homebrew）
brew install git

# 或检查Git路径
which git
```

---

## 📚 相关命令快速参考

### 快速检查命令

```bash
# 检查.env是否被git忽略
git check-ignore .env

# 搜索Git历史中的泄露密钥
git log --all -i -S "sk-" --pretty=format:"%h %s"

# 列出最近6个提交
git log --oneline -6

# 检查当前Git状态
git status
```

### 结合脚本的完整流程

```bash
# 1. 进入项目目录
cd /Users/yuzekun/ai-coding-tutor

# 2. 运行安全检查
bash check_api_key_security.sh

# 3. 更新密钥（如需要）
python api_key_manager.py rotate

# 4. 再次检查
bash check_api_key_security.sh

# 5. 提交更改（如有）
git add .
git commit -m "chore: rotate API key"
git push
```

---

## ✨ 脚本功能总结

脚本会自动：
- ✅ 检查.env被git忽略
- ✅ 扫描Git历史找泄露的密钥
- ✅ 检查代码中的硬编码密钥
- ✅ 验证.env未被提交
- ✅ 生成安全状态报告
- ✅ 给出改进建议

**所有这些只需一个命令！** 🎉

```bash
bash check_api_key_security.sh
```

---

## 🎯 现在就试试

打开终端，运行：

```bash
cd /Users/yuzekun/ai-coding-tutor
bash check_api_key_security.sh
```

你会看到彩色输出的完整安全检查报告！✨


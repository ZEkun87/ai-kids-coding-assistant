# 🚀 快速上传指南 | Quick Upload Guide

## ⚡ 3 步完成上传

### Step 1: 更新联系信息（必须）

```bash
# 在所有文件中替换以下占位符为真实信息：
# - zekunio@outlook.com
# - your-wechat-id  
# - your-username
# - your-website.com (可选)

# 可以使用 sed 批量替换（macOS）：
find . -type f \( -name "*.md" -o -name "*.py" \) -exec sed -i '' 's/zekunio@outlook.com/你的真实邮箱/g' {} +
find . -type f \( -name "*.md" -o -name "*.py" \) -exec sed -i '' 's/your-username/你的GitHub用户名/g' {} +
```

### Step 2: 安全检查（必须）

```bash
# 1. 确认没有硬编码的 API Key
grep -r "sk-[a-zA-Z0-9]" . --include="*.py" --include="*.js" --include="*.jsx"

# 2. 确认 .env 未被跟踪
git check-ignore .env  # 应该有输出

# 3. 验证水印存在
grep -r "KIDS_CODING_TUTOR_2024_AUTHORIZED" . --include="*.py"

# 4. 测试本地运行
cd backend
uvicorn main:app --reload &
curl http://localhost:8000/ | grep "watermark_id"
kill %1
```

### Step 3: 上传到 GitHub

```bash
# 1. 初始化 Git（如果还没有）
git init

# 2. 添加所有文件
git add .

# 3. 提交
git commit -m "Initial commit: AI Kids Coding Assistant v1.0.0

- RAG + Multi-Agent architecture
- Non-commercial license with watermark protection
- Complete documentation and security measures"

# 4. 关联远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/ai-kids-coding-assistant.git

# 5. 推送
git branch -M main
git push -u origin main
```

---

## ✅ 上传后验证

访问: `https://github.com/你的用户名/ai-kids-coding-assistant`

检查清单:
- [ ] README 正确渲染
- [ ] LICENSE 被 GitHub 识别
- [ ] 所有文件都存在
- [ ] 无敏感信息泄露
- [ ] .github 目录存在

---

## 🔍 验证水印

```bash
# 启动服务后测试
curl -I http://localhost:8000/ | grep -E "X-(Project|Copyright|Watermark|License)"
```

应看到:
```
X-Project-Name: 少儿编程智能辅导系统
X-Copyright: Copyright (c) 2024 All Rights Reserved
X-Watermark-ID: KIDS_CODING_TUTOR_2024_AUTHORIZED
X-License: Non-Commercial Use License
```

---

## 📚 重要文档

| 文档 | 用途 |
|------|------|
| README.md | 项目主文档 |
| LICENSE | 非商业许可证 |
| PROTECTION_GUIDE.md | 保护机制详解 |
| GITHUB_UPLOAD_CHECKLIST.md | 详细检查清单 |
| COMPLETION_REPORT.md | 完成报告 |

---

## ⚠️ 注意事项

1. **不要**提交 `.env` 文件
2. **不要**硬编码 API Key
3. **不要**移除水印或版权声明
4. **务必**更新联系信息
5. **建议**先在小范围测试

---

<div align="center">

**祝上传顺利！** 🎉

</div>

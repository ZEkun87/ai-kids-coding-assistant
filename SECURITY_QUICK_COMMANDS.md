# 🚀 安全检查工具 - 快速命令参考

## 最快的方式（复制粘贴）

```bash
cd /Users/yuzekun/ai-coding-tutor && bash check_api_key_security.sh
```

---

## 📋 常用命令速查

| 命令 | 说明 |
|------|------|
| `bash check_api_key_security.sh` | 运行安全检查 |
| `python api_key_manager.py status` | 查看密钥状态 |
| `python api_key_manager.py rotate` | 交互式密钥轮换 |
| `git check-ignore .env` | 验证.env被忽略 |

---

## ✅ 检查成功的标志

看到以下输出就表示安全没问题：

```
✓ .env 已正确配置在.gitignore中
✓ .env文件未被提交到历史
```

---

## ⚠️ 需要注意的信息

```
⚠️ 发现可能的密钥泄露
```

这是**正常的**！因为：
- 旧密钥已被撤销（失效）
- 只需要新密钥配置正确即可
- 可选：查看 CLEAN_GIT_HISTORY.md 清理历史

---

## 🎯 一键三步安全设置

```bash
# 1. 检查当前状态
bash check_api_key_security.sh

# 2. 轮换密钥（输入新密钥）
python api_key_manager.py rotate

# 3. 验证成功
python api_key_manager.py status
```

**5分钟完成！** ⏱️


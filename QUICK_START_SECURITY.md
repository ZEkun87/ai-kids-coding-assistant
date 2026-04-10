# 🔐 API密钥安全 - 快速参考卡

## ⚡ 30秒快速步骤

### 立即做：

1. **撤销旧密钥**（DashScope控制台）✓
   ```
   登录 → API密钥管理 → 删除 sk-e1240d5855d14fceba75c2326158c1c3
   ```

2. **生成新密钥**（DashScope控制台）
   ```
   新建API密钥 → 复制 → 保存安全地方
   ```

3. **更新.env**
   ```bash
   # 使用密钥管理工具（推荐）
   python api_key_manager.py rotate
   
   # 或手动编辑
   nano .env.local  # 或 .env
   # 替换: DASHSCOPE_API_KEY=你的新密钥
   ```

4. **测试**
   ```bash
   python -m uvicorn backend.main:app --reload
   curl http://localhost:8000/
   ```

---

## 📋 完整检查清单

- [ ] 旧密钥已撤销（DashScope）
- [ ] 新密钥已生成
- [ ] .env 或 .env.local 已更新
- [ ] 应用启动成功测试
- [ ] 删除旧.env文件副本
- [ ] (可选) 清理Git历史

---

## 🛠️ 可用工具

### 1. 密钥管理脚本
```bash
# 查看当前状态
python api_key_manager.py status

# 交互式轮换密钥
python api_key_manager.py rotate

# 检查gitignore配置
python api_key_manager.py check
```

### 2. 安全检查脚本
```bash
# 检查是否有密钥泄露
bash check_api_key_security.sh
```

### 3. 手动命令
```bash
# 验证.env被git忽略
git check-ignore .env

# 搜索历史中的泄露密钥
git log --all -i -S "sk-" --pretty=format:"%h %s"

# 创建.env.local（本地开发）
cp .env.local.example .env.local
```

---

## 🔄 密钥轮换流程

### 本地开发
```bash
1. 生成新密钥 (DashScope)
2. python api_key_manager.py rotate
3. 选择 1 (本地环境)
4. 输入新密钥
5. 测试: python -m uvicorn backend.main:app --reload
```

### Docker环境
```bash
1. 更新.env: DASHSCOPE_API_KEY=新密钥
2. docker-compose -f compose.yaml build --no-cache
3. docker-compose -f compose.yaml up
```

### CI/CD环境
```bash
1. 更新CI/CD平台的密钥 (GitHub/GitLab)
2. 下次部署时自动使用
```

---

## ⚠️ 危险操作（谨慎使用）

### 清理Git历史（需要强制推送）

**方案A: BFG（快速）**
```bash
# 安装
brew install bfg

# 清理
bfg --delete-files .env
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送（警告！）
git push origin --force-with-lease --all
```

**方案B: git-filter-branch**
```bash
git filter-branch --tree-filter 'rm -f .env' -- --all
git push origin --force-with-lease --all
```

**方案C: 不修改历史（推荐）**
```bash
# 只需撤销旧密钥，历史保留但密钥已失效
nano .env
# 更新为新密钥，提交
git push origin main
```

---

## 📁 文件位置

```
✅ .env.example            - 安全的标准模板
✅ .env.local.example      - 本地开发模板
✅ .env                    - 你的个人密钥（NOT COMMITTED）
✅ .env.local              - 本地密钥副本（NOT COMMITTED）
✅ .gitignore              - 已配置不提交.env*

📚 API_KEY_SECURITY.md     - 详细安全指南
📚 CLEAN_GIT_HISTORY.md    - Git历史清理指南
📚 api_key_manager.py      - 密钥管理工具
📚 check_api_key_security.sh - 安全检查工具
```

---

## 🚨 如果密钥泄露了

### 立即操作（5分钟内）

```bash
# 步骤1: 撤销旧密钥 (DashScope)
# 登录并删除: sk-e1240d5855d14fceba75c2326158c1c3

# 步骤2: 生成新密钥 (DashScope)
# 创建新密钥

# 步骤3: 更新应用
python api_key_manager.py rotate

# 步骤4: 验证
curl http://localhost:8000/  # 应该返回200
```

### 防御措施（30分钟内）

```bash
# 扫描历史中的密钥
bash check_api_key_security.sh

# 根据需要清理历史
bash CLEAN_GIT_HISTORY.md  # 查看详细步骤
```

---

## 🔐 最佳实践

### ✅ 做这些

- ✅ 使用.env.local用于本地开发
- ✅ 使用环境变量用于部署
- ✅ 每3-6个月轮换密钥
- ✅ 使用密钥管理工具（AWS/HashiCorp）
- ✅ 定期审计密钥使用
- ✅ 安装git-secrets防止意外提交

### ❌ 不要做这些

- ❌ 提交.env到Git
- ❌ 硬编码密钥到源代码
- ❌ 在命令行历史中输入明文密钥
- ❌ 分享未加密的.env文件
- ❌ 使用静态的单一密钥
- ❌ 信任视觉隐藏密钥

---

## 📞 需要帮助？

### 常见问题

**Q: 我忘记了新密钥？**
A: 返回DashScope控制台创建新密钥（旧的已失效）

**Q: 应用启动失败？**
A: 检查: `python api_key_manager.py status`

**Q: Git历史清理失败？**
A: 查看 `CLEAN_GIT_HISTORY.md` - 问题排查部分

**Q: Docker无法连接DashScope？**
A: 确保`DASHSCOPE_API_KEY`在`compose.yaml`中正确配置

---

## 🎯 下一步

1. [ ] 立即撤销旧密钥 (5分钟)
2. [ ] 生成新密钥 (2分钟)
3. [ ] 运行 `python api_key_manager.py rotate` (2分钟)
4. [ ] 测试应用 (1分钟)
5. [ ] (可选) 清理Git历史 (10-30分钟)
6. [ ] 配置git-secrets (5分钟)

**总耗时: ~15-40分钟** ⏱️

---

**现在就开始保护你的API密钥！** 🔐

有问题? 查看详细指南:
- 📚 API_KEY_SECURITY.md 
- 📚 CLEAN_GIT_HISTORY.md

# 🔧 清理Git历史中的API密钥 - 快速指南

## ⚠️ 检查结果：找到Git历史泄露

根据扫描，你的API密钥在以下提交中被暴露：
- `5c5ac5e` Refactor backend...
- `97d87ad` Enhance agent workflow...
- `d689fd9` Refactor main.py...
- `90bc7a8` feat: 优化向量库...
- `18a3bb0` 修改说明...
- `20f22fe` Initial commit...

**⚠️ 重要：这意味着任何看到这些提交的人都可能看到你的API密钥！**

---

## 🚨 立即采取行动

### 步骤1: 撤销旧密钥（**现在就做**）

**访问 DashScope 控制台**:
1. 打开 https://dashscope.console.aliyun.com
2. 登录你的账户
3. 进入"API密钥管理"
4. 找到并删除密钥: `sk-e1240d5855d14fceba75c2326158c1c3`
5. **点击删除/撤销**

**旧密钥立即失效！** ✓

### 步骤2: 生成新密钥
1. 在DashScope控制台创建新密钥
2. 复制新密钥（只会显示一次！）
3. 保存到密码管理器

### 步骤3: 选择清理方案

有两种方案清理Git历史：

---

## 方案A: 使用 BFG Repo-Cleaner（推荐 - 简单快速）

### 安装BFG
```bash
# macOS
brew install bfg

# Ubuntu/Debian
apt-get install bfg

# 或从官网下载: https://rtyley.github.io/bfg-repo-cleaner/
```

### 清理步骤

```bash
# 1. 创建一个干净的克隆作为备份
cd ..
git clone --mirror ai-coding-tutor ai-coding-tutor.git.bak

# 2. 返回项目目录
cd ai-coding-tutor

# 3. 更新.env为新密钥
nano .env
# 替换为新API密钥

# 4. 使用BFG删除历史中的密钥
bfg --replace-text passwords.txt

# 或者直接删除.env文件历史（如果有的话）
bfg --delete-files .env

# 5. 完成清理
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 6. 强制推送到远程（谨慎！）
git push origin --force --all
```

### 创建passwords.txt文件

如果想替换特定的密钥值而不是完全删除文件，创建：

```bash
# passwords.txt
sk-e1240d5855d14fceba75c2326158c1c3==>[DELETED]
```

然后运行：
```bash
bfg --replace-text passwords.txt
```

---

## 方案B: 使用 git-filter-branch（标准但较慢）

```bash
# 1. 更新.env为新密钥
nano .env

# 2. 从所有提交中删除.env文件
git filter-branch --tree-filter 'rm -f .env' -- --all

# 3. 清理引用日志
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. 强制推送
git push origin --force --all --tags
```

---

## 方案C: 简单保险的方案（不改Git历史）

如果你不想修改Git历史（可能有其他团队成员），只需：

```bash
# 1. 生成新密钥
# (已在DashScope撤销了旧密钥)

# 2. 更新.env为新密钥
nano .env
# 替换为新API密钥

# 3. 创建新提交
git add .env
git commit -m "chore: rotate API key"

# 4. 提交推送
git push origin main
```

**优点**:
- 更安全，不修改历史
- 其他开发者不受影响

**缺点**:
- 旧密钥仍在历史中（但已被撤销）
- 克隆旧提交时密钥已无效

---

## 检查清理是否成功

### 验证1: 检查历史中是否还有密钥
```bash
git log --all --full-history -i -S "sk-" --pretty=format:"%h %s"
# 应该返回空
```

### 验证2: 检查当前.env
```bash
cat .env
# 应该显示新密钥
```

### 验证3: 验证应用启动
```bash
python -m uvicorn backend.main:app --reload
# 应该正常启动
```

### 验证4: 测试API
```bash
curl http://localhost:8000/
# 应该返回200 OK
```

---

## 📝 更新远程仓库

### 对于GitHub

**危险操作警告：** 如果使用BFG修改了历史，需要强制推送

```bash
# 1. 确认所有本地提交正确
git log --oneline | head -10

# 2. 强制推送（覆盖远程历史）
git push origin --force-with-lease --all
git push origin --force-with-lease --tags

# 3. 通知团队成员更新本地克隆
# 他们需要运行:
git fetch --all --prune
git reset --hard origin/main
```

### 对于其他Git服务

根据你的Git服务调整强制推送权限：
- GitHub: Settings → Branches → 允许强制推送
- GitLab: Settings → Protected branches
- Gitea/其他: 检查分支保护设置

---

## 🔒 防止将来的泄露

### 安装Git钩子检查

```bash
# 创建pre-commit钩子
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# 防止提交.env文件
if git diff --cached --name-only | grep -E "^\\.env"; then
    echo "❌ 错误：检测到.env文件将被提交！"
    echo "✅ .env应该在.gitignore中"
    exit 1
fi

# 防止提交包含密钥的文件
if git diff --cached -S "sk-" | grep -q "sk-"; then
    echo "❌ 错误：检测到API密钥将被提交！"
    exit 1
fi

exit 0
EOF

chmod +x .git/hooks/pre-commit
```

### 使用git-secrets工具

```bash
# 安装
brew install git-secrets

# 安装钩子
git secrets --install

# 配置检查规则
git secrets --register-aws
git secrets --add 'sk-[0-9a-f]{30,}'  # DashScope密钥格式

# 检查现有历史
git secrets --scan-history
```

---

## 🚀 快速检查清单

在清理后确认以下事项：

- [ ] **撤销旧API密钥** (DashScope控制台)
- [ ] **生成新API密钥**
- [ ] **更新.env文件** 为新密钥
- [ ] **选择清理方案** (BFG / git-filter-branch / 不修改历史)
- [ ] **执行清理** (如果选择修改历史)
- [ ] **验证** git log中没有旧密钥
- [ ] **强制推送** (如果修改了历史)
- [ ] **测试应用** 确保新密钥有效
- [ ] **通知团队** 密钥已轮换和历史已清理
- [ ] **配置git钩子** 防止未来泄露

---

## 🆘 遇到问题？

### 问题1: 强制推送被拒绝
```
remote: GitLab: You are not allowed to force push code to this branch
```

**解决方案**:
- 在Git服务的分支保护设置中临时禁用
- 或联系管理员
- 清理完后重新启用

### 问题2: BFG找不到匹配的密钥
```bash
# 确保密钥格式正确
git log --all -i -S "sk-" | head -5

# 更新passwords.txt并重试
bfg --replace-text passwords.txt
```

### 问题3: 清理后丢失提交
```bash
# 检查备份
ls -la ../ai-coding-tutor.git.bak

# 恢复
git clone ../ai-coding-tutor.git.bak ai-coding-tutor-restored
```

---

## 📚 参考资源

- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-branch](https://git-scm.com/docs/git-filter-branch)
- [GitHub - Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [git-secrets](https://github.com/awslabs/git-secrets)

---

**现在就开始！先撤销旧密钥，然后选择清理方案。** 🔐


#!/bin/bash

# API密钥安全检查脚本
# 用途：检查Git历史中是否有泄露的API密钥

set -e

echo "🔍 API密钥安全检查工具"
echo "======================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查1: 当前.env文件是否在.gitignore中
echo -e "${BLUE}[检查1] 验证.env是否在.gitignore中...${NC}"
if git check-ignore .env .env.local .env.local.example 2>/dev/null | grep -q ".env"; then
    echo -e "${GREEN}✓ .env 已正确配置在.gitignore中${NC}"
else
    echo -e "${RED}✗ .env 未在.gitignore中！添加方式：${NC}"
    echo "   echo '.env' >> .gitignore"
fi
echo ""

# 检查2: 搜索Git历史中的密钥模式
echo -e "${BLUE}[检查2] 扫描Git历史中的API密钥模式...${NC}"

# DashScope密钥模式: sk-开头
LEAKED_KEYS=$(git log --all --full-history --source --remotes -i -S "sk-" --pretty=format:"%h %s" 2>/dev/null || true)

if [ -n "$LEAKED_KEYS" ]; then
    echo -e "${RED}⚠️  发现可能的密钥泄露（DashScope格式）:${NC}"
    echo "$LEAKED_KEYS"
    echo ""
    echo -e "${YELLOW}考虑使用以下工具清理:${NC}"
    echo "  • BFG Repo-Cleaner: https://rtyley.github.io/bfg-repo-cleaner/"
    echo "  • git-filter-branch: https://git-scm.com/docs/git-filter-branch"
else
    echo -e "${GREEN}✓ Git历史中未找到DashScope密钥泄露${NC}"
fi
echo ""

# 检查3: 当前分支中是否有明文密钥
echo -e "${BLUE}[检查3] 扫描当前文件中的硬编码密钥...${NC}"

HARDCODED=$(grep -r "DASHSCOPE_API_KEY" --include="*.py" --include="*.yaml" --include="*.yml" --include="*.json" . 2>/dev/null | grep -v ".git" | grep -v "your_" | grep -v "example" | grep -v ".example" | grep -v "sk-" || true)

if [ -n "$HARDCODED" ]; then
    echo -e "${YELLOW}⚠️  发现硬编码的DASHSCOPE_API_KEY配置:${NC}"
    echo "$HARDCODED"
    echo ""
    echo -e "${YELLOW}建议: 移除硬编码值，使用环境变量替代${NC}"
else
    echo -e "${GREEN}✓ 未发现硬编码的明文API密钥${NC}"
fi
echo ""

# 检查4: .env文件是否被提交
echo -e "${BLUE}[检查4] 检查.env文件提交历史...${NC}"

ENV_COMMITTED=$(git log --all --full-history -- .env 2>/dev/null | wc -l)

if [ "$ENV_COMMITTED" -gt 0 ]; then
    echo -e "${RED}✗ .env文件已被提交到Git历史!${NC}"
    echo "  找到 $ENV_COMMITTED 次提交"
    echo ""
    echo -e "${YELLOW}清理步骤:${NC}"
    echo "  1. 撤销旧API密钥 (DashScope控制台)"
    echo "  2. 生成新API密钥"
    echo "  3. 使用BFG或git-filter-branch从历史中删除.env"
    echo "  4. 更新.env文件为新密钥"
    echo ""
    echo -e "${YELLOW}使用BFG清理（推荐）:${NC}"
    echo "  bfg --delete-files .env"
    echo "  git reflog expire --expire=now --all && git gc --prune=now --aggressive"
else
    echo -e "${GREEN}✓ .env文件未被提交到历史${NC}"
fi
echo ""

# 检查5: 建议的安全状态
echo -e "${BLUE}[检查5] 安全状态总结${NC}"
echo "======================================"
echo ""
echo "✅ 好的做法:"
echo "  • 使用.env.local用于本地开发"
echo "  • 所有.env*文件在.gitignore中"
echo "  • 使用环境变量进行配置"
echo "  • 定期轮换API密钥"
echo ""
echo "❌ 不安全的做法:"
echo "  • 提交.env到版本控制"
echo "  • 硬编码密钥到源代码"
echo "  • 在命令行历史中输入明文密钥"
echo "  • 分享未加密的.env文件"
echo ""

echo -e "${GREEN}检查完成!${NC}"
echo ""
echo "📚 更多信息，请查看: API_KEY_SECURITY.md"

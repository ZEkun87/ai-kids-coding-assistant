#!/bin/bash

# ============================================
# Upload AI-KIDS-CODING-ASSISTANT to New GitHub Repository
# ============================================

echo "🚀 Uploading AI-KIDS-CODING-ASSISTANT to GitHub"
echo "================================================"
echo ""

# Configuration - UPDATE THESE VALUES
NEW_REPO_URL="https://github.com/YOUR_USERNAME/ai-kids-coding-assistant.git"
BRANCH_NAME="main"

echo "⚠️  IMPORTANT: Please update NEW_REPO_URL in this script first!"
echo "   Current value: $NEW_REPO_URL"
echo ""
echo "Steps to complete:"
echo "1. Create a new repository on GitHub (don't initialize with README)"
echo "2. Copy the repository URL from GitHub"
echo "3. Update NEW_REPO_URL in this script"
echo "4. Run this script again"
echo ""

# Check if user wants to proceed
read -p "Have you updated the NEW_REPO_URL? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Please update the NEW_REPO_URL first, then run this script again."
    exit 1
fi

echo ""
echo "📋 Starting upload process..."
echo ""

# Step 1: Verify we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: README.md not found. Are you in the correct directory?"
    exit 1
fi

echo "✅ Project directory verified"

# Step 2: Check git status
echo ""
echo "🔍 Checking git status..."
git status --short

# Step 3: Ensure all changes are committed
echo ""
echo "💾 Committing any uncommitted changes..."
git add -A
git commit -m "Final preparation before uploading to new repository" || echo "No changes to commit"

# Step 4: Remove old remote
echo ""
echo "🔄 Removing old remote repository..."
git remote remove origin 2>/dev/null || echo "No existing remote to remove"

# Step 5: Add new remote
echo ""
echo "➕ Adding new remote repository..."
git remote add origin "$NEW_REPO_URL"
echo "✅ New remote added: $NEW_REPO_URL"

# Step 6: Push to new repository
echo ""
echo "📤 Pushing to new repository..."
git branch -M "$BRANCH_NAME"
git push -u origin "$BRANCH_NAME"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Project uploaded to GitHub!"
    echo ""
    echo "🎉 Your project is now available at:"
    echo "   $NEW_REPO_URL"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Visit your repository on GitHub"
    echo "   2. Add topics/tags for better discoverability"
    echo "   3. Set up GitHub Pages (optional)"
    echo "   4. Enable Issues and Discussions"
    echo "   5. Add repository description and website URL"
    echo ""
else
    echo ""
    echo "❌ Error occurred during push."
    echo ""
    echo "Common issues:"
    echo "   1. Wrong repository URL"
    echo "   2. Authentication required (use GitHub token or SSH)"
    echo "   3. Repository doesn't exist"
    echo ""
    echo "Try these solutions:"
    echo "   - Verify the repository URL is correct"
    echo "   - Make sure you're authenticated: gh auth login"
    echo "   - Try using SSH URL instead: git@github.com:USERNAME/REPO.git"
    echo ""
    exit 1
fi

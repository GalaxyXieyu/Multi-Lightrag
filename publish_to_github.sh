#!/bin/bash

# 🚀 LightRAG Enhanced 发布脚本
# 使用方法: ./publish_to_github.sh [your-github-username] [repository-name]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 参数检查
if [ $# -ne 2 ]; then
    echo -e "${RED}❌ 使用方法: $0 [your-github-username] [repository-name]${NC}"
    echo -e "${YELLOW}💡 例如: $0 yourusername LightRAG-Enhanced${NC}"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME=$2
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo -e "${BLUE}🌟 LightRAG Enhanced 发布脚本${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "📦 仓库: ${GITHUB_USERNAME}/${REPO_NAME}"
echo -e "🔗 URL: ${REPO_URL}"
echo ""

# 检查是否已经有远程仓库
if git remote get-url origin >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  检测到已有远程仓库，正在更新...${NC}"
    git remote set-url origin $REPO_URL
else
    echo -e "${GREEN}➕ 添加远程仓库...${NC}"
    git remote add origin $REPO_URL
fi

# 创建并推送标签
echo -e "${GREEN}🏷️  创建版本标签...${NC}"
git tag -a v1.3.10-enhanced -m "🌟 LightRAG Enhanced v1.3.10-enhanced

🎯 重构核心特性:
- 多图谱架构支持
- 智能实体合并系统
- 图谱状态管理
- 异步批处理优化
- 智能缓存系统
- 现代化界面设计

📋 技术亮点:
- 24个完整API端点
- 支持多种合并策略
- 实时状态同步
- 响应式用户体验

🙏 基于 HKUDS/LightRAG 深度重构"

# 推送代码和标签
echo -e "${GREEN}🚀 推送代码到 GitHub...${NC}"
git push -u origin main

echo -e "${GREEN}🏷️  推送标签...${NC}"
git push origin v1.3.10-enhanced

echo ""
echo -e "${GREEN}✅ 发布成功！${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "🎉 您的 LightRAG Enhanced 已成功发布到 GitHub！"
echo ""
echo -e "${YELLOW}📋 下一步操作:${NC}"
echo -e "1. 访问: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
echo -e "2. 创建 Release: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/releases/new"
echo -e "3. 设置仓库描述和标签"
echo -e "4. 添加 Topics: knowledge-graph, rag, multi-graph, entity-merging"
echo ""
echo -e "${GREEN}🌟 Release 标题建议:${NC}"
echo -e "LightRAG Enhanced v1.3.10-enhanced - 多图谱知识图谱重构版"
echo ""
echo -e "${GREEN}📝 Release 描述模板已保存在 RELEASE_GUIDE.md 中${NC}"
echo ""
echo -e "${BLUE}🎯 感谢使用 LightRAG Enhanced！${NC}"

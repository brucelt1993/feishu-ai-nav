#!/bin/bash
# ============================================
# 飞书AI导航 - Docker 部署脚本
# GitHub: https://github.com/brucelt1993/feishu-ai-nav.git
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 项目目录（脚本所在目录）
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

log_info "========== 开始部署 =========="
log_info "项目目录: $PROJECT_DIR"

# 1. 拉取最新代码
log_info "拉取最新代码..."
git fetch origin
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main 2>/dev/null || git rev-parse origin/master)

if [ "$LOCAL" = "$REMOTE" ]; then
    log_info "代码已是最新版本"
else
    log_info "发现新版本，正在更新..."
    git pull origin main 2>/dev/null || git pull origin master
    log_info "代码更新完成"
fi

# 2. 检查 .env 文件
if [ ! -f ".env" ]; then
    log_warn ".env 文件不存在，从模板创建..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_warn "请编辑 .env 文件配置必要参数后重新运行"
        exit 1
    fi
fi

# 3. 构建并启动容器
log_info "构建 Docker 镜像..."
docker-compose build --no-cache

log_info "停止旧容器..."
docker-compose down --remove-orphans 2>/dev/null || true

log_info "启动新容器..."
docker-compose up -d

# 4. 等待服务就绪
log_info "等待服务启动..."
sleep 5

# 5. 健康检查
log_info "检查服务状态..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log_info "后端服务: 运行中 (http://localhost:8000)"
else
    log_warn "后端服务: 启动中或异常，请检查日志"
fi

if curl -s http://localhost:3008 > /dev/null 2>&1; then
    log_info "前端服务: 运行中 (http://localhost:3008)"
else
    log_warn "前端服务: 启动中或异常，请检查日志"
fi

# 6. 显示容器状态
echo ""
log_info "========== 容器状态 =========="
docker-compose ps

echo ""
log_info "========== 部署完成 =========="
log_info "前端地址: http://localhost:3008"
log_info "后端地址: http://localhost:8000"
log_info "查看日志: docker-compose logs -f"

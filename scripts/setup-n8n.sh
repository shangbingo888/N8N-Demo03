#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# n8n 2.5.0 Docker 重新部署脚本
# ============================================================
# 功能：
#   1. 停止旧 n8n 容器（保留容器和数据卷，不删除）
#   2. 拉取 n8nio/n8n:2.5.0 镜像
#   3. 启动新容器（数据持久化、端口 7890、自动重启）
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OLD_CONTAINER_NAME="n8n-2.5.0"
IMAGE="n8nio/n8n:2.5.0"
DATA_DIR="${SCRIPT_DIR}/n8n-data"
FILES_DIR="${SCRIPT_DIR}/n8n-files"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ---------- 步骤 1：停止旧容器（不删除） ----------
log_info "步骤 1/5：停止旧 n8n 容器（保留容器和数据，不删除）..."

STOPPED_COUNT=0

# 1a. 按名称停止并重命名旧容器（释放名称供新容器使用）
if docker ps -a --format '{{.Names}}' | grep -qx "${OLD_CONTAINER_NAME}"; then
    IS_RUNNING=$(docker ps --format '{{.Names}}' | grep -qx "${OLD_CONTAINER_NAME}" && echo "true" || echo "false")
    if [ "$IS_RUNNING" = "true" ]; then
        docker stop "${OLD_CONTAINER_NAME}" 2>/dev/null && STOPPED_COUNT=$((STOPPED_COUNT + 1)) || true
    fi
    BACKUP_NAME="${OLD_CONTAINER_NAME}-backup-$(date +%Y%m%d-%H%M%S)"
    docker rename "${OLD_CONTAINER_NAME}" "${BACKUP_NAME}"
    log_info "旧容器已重命名为 ${BACKUP_NAME}（保留不删除）"
fi

# 1b. 按镜像查找其他 n8n 容器，只停止不删除
OLD_IDS=$(docker ps --filter ancestor=n8nio/n8n --format '{{.ID}}' 2>/dev/null || true)
for cid in ${OLD_IDS}; do
    cname=$(docker inspect --format '{{.Name}}' "$cid" | sed 's|^/||')
    log_warn "发现正在运行的其他 n8n 容器: ${cname} (${cid})，正在停止 ..."
    docker stop "$cid" 2>/dev/null && STOPPED_COUNT=$((STOPPED_COUNT + 1)) || true
done

log_info "已停止 ${STOPPED_COUNT} 个运行中的容器，所有旧容器均已保留"

# ---------- 步骤 2：确保数据目录存在 ----------
log_info "步骤 2/5：检查数据目录 ..."
mkdir -p "${DATA_DIR}"
mkdir -p "${FILES_DIR}"

if [ -f "${DATA_DIR}/database.sqlite" ]; then
    log_info "检测到现有数据库，数据将被保留 ✓"
else
    log_info "首次部署，将初始化新数据库"
fi

# ---------- 步骤 3：拉取镜像 ----------
log_info "步骤 3/5：准备镜像 ${IMAGE} ..."

if docker image inspect "${IMAGE}" >/dev/null 2>&1; then
    log_info "镜像 ${IMAGE} 已存在，跳过拉取 ✓"
else
    # 优先尝试直接拉取
    if docker pull "${IMAGE}" 2>/dev/null; then
        log_info "直接拉取成功 ✓"
    elif command -v crane &>/dev/null; then
        # 回退：使用 crane 通过代理下载
        log_warn "Docker pull 失败，尝试用 crane 通过代理下载..."
        HTTPS_PROXY="${HTTPS_PROXY:-http://127.0.0.1:7897}" \
        HTTP_PROXY="${HTTP_PROXY:-http://127.0.0.1:7897}" \
            crane pull "${IMAGE}" "${SCRIPT_DIR}/n8n-temp.tar" 2>/dev/null || {
            log_error "crane 下载失败"
            exit 1
        }
        docker load < "${SCRIPT_DIR}/n8n-temp.tar" 2>/dev/null || {
            log_error "镜像导入失败"
            exit 1
        }
        rm -f "${SCRIPT_DIR}/n8n-temp.tar"
        log_info "通过 crane 拉取成功 ✓"
    else
        log_error "镜像拉取失败，且 crane 未安装。请手动执行:"
        log_error "  brew install crane"
        log_error "  HTTPS_PROXY=http://127.0.0.1:7897 crane pull ${IMAGE} n8n-2.5.0.tar"
        log_error "  docker load < n8n-2.5.0.tar"
        exit 1
    fi
fi

# ---------- 步骤 4：生成加密密钥（如未设置） ----------
if [ ! -f "${SCRIPT_DIR}/.env" ] || grep -q "change-me-to-a-random-string" "${SCRIPT_DIR}/.env" 2>/dev/null; then
    log_info "步骤 4/5：生成安全的加密密钥 ..."
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    cat > "${SCRIPT_DIR}/.env" <<EOF
# n8n 加密密钥（自动生成于 $(date '+%Y-%m-%d %H:%M:%S')）
# ⚠️ 请妥善保管，丢失后无法恢复现有凭证
N8N_ENCRYPTION_KEY=${ENCRYPTION_KEY}
EOF
    log_info "加密密钥已生成并写入 .env ✓"
else
    log_info "步骤 4/5：使用现有加密密钥 ✓"
fi

# ---------- 步骤 5：启动容器 ----------
log_info "步骤 5/5：启动 n8n 2.5.0 容器 ..."

docker run -d \
    --name "${OLD_CONTAINER_NAME}" \
    --restart unless-stopped \
    -p 7890:5678 \
    -e N8N_HOST=localhost \
    -e N8N_PORT=5678 \
    -e N8N_PROTOCOL=http \
    -e NODE_ENV=production \
    -e TZ=Asia/Shanghai \
    -e GENERIC_TIMEZONE=Asia/Shanghai \
    -e N8N_ENCRYPTION_KEY="$(grep N8N_ENCRYPTION_KEY "${SCRIPT_DIR}/.env" | cut -d= -f2-)" \
    -v "${DATA_DIR}:/home/node/.n8n" \
    -v "${FILES_DIR}:/files" \
    "${IMAGE}"

log_info "容器启动命令已执行，等待就绪 ..."

# ---------- 启动后检查 ----------
sleep 3

if docker ps --format '{{.Names}}' | grep -qx "${OLD_CONTAINER_NAME}"; then
    CONTAINER_ID=$(docker ps --filter "name=${OLD_CONTAINER_NAME}" --format '{{.ID}}' | head -1)
    log_info "============================================"
    log_info "  n8n 2.5.0 部署成功！"
    log_info "============================================"
    log_info "  容器名称 : ${OLD_CONTAINER_NAME}"
    log_info "  容器 ID  : ${CONTAINER_ID}"
    log_info "  访问地址 : http://localhost:7890"
    log_info "  数据目录 : ${DATA_DIR}"
    log_info "  文件目录 : ${FILES_DIR}"
    log_info "============================================"
    log_info ""
    log_info "查看日志：  docker logs -f ${OLD_CONTAINER_NAME}"
    log_info "停止容器：  docker stop ${OLD_CONTAINER_NAME}"
    log_info "启动容器：  docker start ${OLD_CONTAINER_NAME}"
    log_info ""
    log_warn "⚠️  提醒：首次启动后请在 n8n UI 中创建账号。"
    log_warn "⚠️  提醒：更新 .mcp.json 中的 N8N_API_URL 为 http://localhost:7890"
else
    log_error "容器启动失败，请查看日志："
    docker logs "${OLD_CONTAINER_NAME}" 2>/dev/null || echo "无法获取日志"
    exit 1
fi

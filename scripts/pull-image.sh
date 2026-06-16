#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# 通过主机代理下载 n8n:2.5.0 镜像并导入 Docker
# ============================================================
# 绕过 Docker daemon 网络问题，使用主机 curl+代理下载后 docker load

IMAGE="n8nio/n8n"
TAG="2.5.0"
PROXY="http://127.0.0.1:7897"
OUTPUT_FILE="n8n-2.5.0.tar"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ---- 方法 1：借助代理容器拉取（推荐） ----
pull_via_proxy_container() {
    log_info "方案一：启动临时代理容器拉取镜像..."

    # 检查代理是否可达
    if ! curl -s --connect-timeout 3 -x "${PROXY}" https://registry-1.docker.io/v2/ > /dev/null 2>&1; then
        # 尝试无代理直接拉取
        log_info "代理不可用，尝试直接拉取..."
        docker pull "${IMAGE}:${TAG}" && return 0
        return 1
    fi

    # 使用代理容器：创建一个使用主机代理的临时 alpine 容器来拉取
    # 在容器内设置代理环境变量
    docker run --rm \
        -e HTTP_PROXY="${PROXY}" \
        -e HTTPS_PROXY="${PROXY}" \
        -e http_proxy="${PROXY}" \
        -e https_proxy="${PROXY}" \
        -v /var/run/docker.sock:/var/run/docker.sock \
        docker:cli \
        pull "${IMAGE}:${TAG}" 2>&1
}

# ---- 方法 2：使用 crane 工具（Go 编写，走系统代理） ----
pull_via_crane() {
    log_info "方案二：使用 crane 工具..."

    # 检查是否已安装 crane
    if ! command -v crane &>/dev/null; then
        log_info "安装 crane（Google Go 容器工具）..."
        if command -v brew &>/dev/null; then
            brew install crane 2>&1 | tail -5
        else
            log_error "需要 Homebrew，请先安装: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            return 1
        fi
    fi

    # crane 会使用系统代理环境变量
    HTTPS_PROXY="${PROXY}" HTTP_PROXY="${PROXY}" \
        crane pull "${IMAGE}:${TAG}" "${OUTPUT_FILE}" 2>&1

    log_info "导入镜像到 Docker..."
    docker load < "${OUTPUT_FILE}" 2>&1
    rm -f "${OUTPUT_FILE}"
}

# ---- 方法 3：手动下载层再组装 ----
pull_via_manual() {
    log_info "方案三：手动下载镜像层并组装..."

    TOKEN=$(curl -s -x "${PROXY}" "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${IMAGE}:pull" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null)
    
    if [ -z "$TOKEN" ]; then
        log_error "无法获取 Docker Hub token"
        return 1
    fi

    # 下载 manifest
    MANIFEST=$(curl -s -x "${PROXY}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
        "https://registry-1.docker.io/v2/${IMAGE}/manifests/${TAG}")

    # 下载 config
    CONFIG_DIGEST=$(echo "$MANIFEST" | python3 -c "import sys,json; print(json.load(sys.stdin)['config']['digest'])" 2>/dev/null)
    mkdir -p blobs
    curl -sL -x "${PROXY}" \
        -H "Authorization: Bearer ${TOKEN}" \
        "https://registry-1.docker.io/v2/${IMAGE}/blobs/${CONFIG_DIGEST}" \
        -o "blobs/$(echo ${CONFIG_DIGEST} | tr ':' '-')"

    # 下载所有 layers
    LAYERS=$(echo "$MANIFEST" | python3 -c "
import sys,json
m=json.load(sys.stdin)
for l in m['layers']:
    print(l['digest'])
" 2>/dev/null)

    for digest in $LAYERS; do
        fname="blobs/$(echo ${digest} | tr ':' '-')"
        if [ -f "$fname" ]; then
            log_info "跳过已存在的层: ${digest}"
            continue
        fi
        log_info "下载层: ${digest} ..."
        curl -sL -x "${PROXY}" \
            -H "Authorization: Bearer ${TOKEN}" \
            "https://registry-1.docker.io/v2/${IMAGE}/blobs/${digest}" \
            -o "$fname"
    done

    # 组装 OCI layout
    mkdir -p oci-layout
    echo '{"imageLayoutVersion":"1.0.0"}' > oci-layout/oci-layout
    # 简化处理：直接用 crane 打包已下载的 blobs
    log_info "组装并导入..."
    tar -cf "${OUTPUT_FILE}" -C blobs . 2>/dev/null
    docker load < "${OUTPUT_FILE}" 2>&1 && rm -rf blobs oci-layout "${OUTPUT_FILE}" && return 0

    log_error "手动组装失败"
    return 1
}

# ---- 主流程 ----
log_info "开始拉取 ${IMAGE}:${TAG} ..."
log_info ""

# 检查是否已存在
if docker image inspect "${IMAGE}:${TAG}" >/dev/null 2>&1; then
    log_info "镜像 ${IMAGE}:${TAG} 已存在，跳过拉取"
    exit 0
fi

# 方法 1：直接拉取（可能镜像加速器已修复）
if docker pull "${IMAGE}:${TAG}" 2>/dev/null; then
    log_info "直接拉取成功 ✓"
    exit 0
fi

# 方法 2：使用 crane
if pull_via_crane; then
    log_info "通过 crane 拉取成功 ✓"
    exit 0
fi

# 方法 3：代理容器
if pull_via_proxy_container; then
    log_info "通过代理容器拉取成功 ✓"
    exit 0
fi

log_error "所有方法均失败，请检查网络后重试"
exit 1

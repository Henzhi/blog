#!/usr/bin/env bash
# 构建并上传站点到腾讯云轻量服务器（本地构建 + 上传，最省服务器资源）
# 用法：bash scripts/deploy.sh
set -euo pipefail

# ====== 按需修改 ======
SERVER="root@82.156.238.96"   # 服务器 SSH 地址（改成你的 用户名@IP）
REMOTE_DIR="/srv/blog"
# ======================

echo ">> 构建站点..."
npm run build

echo ">> 上传 dist 到 ${SERVER}:${REMOTE_DIR} ..."
rsync -avz --delete ./dist/ "${SERVER}:${REMOTE_DIR}/"

echo ">> 完成。访问 http://82.156.238.96"

#!/usr/bin/env bash
#
# 一键发布：本地构建 → 打包 → 上传到 Lighthouse 服务器
#
# 用法：
#   bash scripts/publish.sh
#
# 依赖：npm（本地已装过依赖）、ssh、tar
# 前提：本机能免密 SSH 到 $SERVER（见 README「配置 SSH 免密」一节）

set -euo pipefail

cd "$(dirname "$0")/.."

SERVER="${SERVER:-tencent}"          # ~/.ssh/config 里的主机别名
REMOTE_DIR="${REMOTE_DIR:-/srv/blog}" # 服务器上的发布目录
SITE_URL="${SITE_URL:-http://82.156.238.96}"
TARBALL="/tmp/blog-publish-$$.tar.gz"

echo "▸ [1/4] 构建站点…"
# env -u 用于绕过某些沙箱环境对构建的干扰，普通终端下无副作用
env -u CODEBUDDY_SESSION_ID -u CLAUDE_SESSION_ID npm run build

echo "▸ [2/4] 打包 dist…"
tar czf "$TARBALL" -C dist .
echo "  产物大小: $(du -h "$TARBALL" | cut -f1)"

echo "▸ [3/4] 上传到 $SERVER:$REMOTE_DIR …"
# 注意：Caddy 以只读方式挂载了 /srv/blog，所以只能清空内容后覆盖，
# 不能整目录替换（换目录会让容器里的挂载点指向旧 inode，页面不会更新）。
cat "$TARBALL" | ssh "$SERVER" "rm -rf ${REMOTE_DIR}/* && tar xzf - -C ${REMOTE_DIR}"
rm -f "$TARBALL"

echo "▸ [4/4] 验证线上…"
CODE=$(curl -s -o /dev/null -w '%{http_code}' -m 15 "$SITE_URL/")
if [ "$CODE" = "200" ]; then
  echo "✅ 发布完成 → $SITE_URL"
else
  echo "⚠️  发布后首页返回 $CODE，请检查：ssh $SERVER 'docker ps --filter name=blog-caddy'"
  exit 1
fi

#!/usr/bin/env bash
#
# 本地部署：构建静态站点并在本机起 HTTP 服务
#
# 用法：
#   bash scripts/serve-local.sh          # 构建 + 启动（默认 http://localhost:4321）
#   PORT=8080 bash scripts/serve-local.sh
#   SKIP_BUILD=1 bash scripts/serve-local.sh   # 跳过构建，直接伺服现有 dist/
#
# 停止：bash scripts/serve-local.sh stop
# 状态：bash scripts/serve-local.sh status

set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${PORT:-4321}"
DIST="$(pwd)/dist"
PIDFILE="/tmp/blog-local-server.pid"
LOGFILE="/tmp/blog-local-server.log"

# ---------- 子命令 ----------
case "${1:-start}" in
  stop)
    if [ -f "$PIDFILE" ]; then
      PID=$(cat "$PIDFILE")
      if kill -0 "$PID" 2>/dev/null; then
        kill "$PID" 2>/dev/null || true
        sleep 1
        kill -9 "$PID" 2>/dev/null || true
        echo "▸ 已停止本地服务 (PID $PID)"
      else
        echo "▸ 进程 $PID 已不在运行"
      fi
      rm -f "$PIDFILE"
    else
      echo "▸ 没有找到运行记录（$PIDFILE）"
    fi
    exit 0
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "▸ 运行中：http://localhost:$PORT  (PID $(cat "$PIDFILE"))"
    else
      echo "▸ 未运行"
    fi
    exit 0
    ;;
  start) ;;
  *)
    echo "未知参数：$1（可用：start / stop / status）" >&2
    exit 1
    ;;
esac

# ---------- 若已在运行，先停掉 ----------
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "▸ 检测到旧进程 $(cat "$PIDFILE")，先停止"
  kill "$(cat "$PIDFILE")" 2>/dev/null || true
  sleep 1
  rm -f "$PIDFILE"
fi

# ---------- 构建 ----------
if [ "${SKIP_BUILD:-0}" != "1" ]; then
  echo "▸ [1/3] 构建站点…"
  # env -u 用于绕过某些沙箱环境对构建的干扰，普通终端下无副作用
  env -u CODEBUDDY_SESSION_ID -u CLAUDE_SESSION_ID npm run build
else
  echo "▸ [1/3] 跳过构建（SKIP_BUILD=1）"
fi

if [ ! -f "$DIST/index.html" ]; then
  echo "✗ dist/index.html 不存在，构建可能失败了" >&2
  exit 1
fi

# ---------- 选一个可用的 Python ----------
PY=""
for cand in \
  "C:/Users/MaHuhu/.workbuddy/binaries/python/versions/3.13.12/python.exe" \
  "C:/Tools/miniconda3/python.exe" \
  "$(command -v python 2>/dev/null || true)" \
  "$(command -v python3 2>/dev/null || true)"
do
  if [ -n "$cand" ] && [ -x "$cand" ]; then PY="$cand"; break; fi
done

if [ -z "$PY" ]; then
  echo "✗ 没找到可用的 Python，无法启动静态服务" >&2
  exit 1
fi

# ---------- 启动 ----------
echo "▸ [2/3] 启动静态服务器（端口 $PORT）…"
cd "$DIST"
nohup "$PY" -m http.server "$PORT" --bind 127.0.0.1 >"$LOGFILE" 2>&1 &
echo $! >"$PIDFILE"
cd - >/dev/null

# ---------- 健康检查 ----------
echo "▸ [3/3] 健康检查…"
sleep 2
OK=0
for path in "/" "/posts/" "/categories/" "/about/";
do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "http://localhost:$PORT$path" || echo "000")
  printf "   %-12s %s\n" "$path" "$CODE"
  [ "$CODE" = "200" ] && OK=$((OK + 1))
done

if [ "$OK" -eq 0 ]; then
  echo "✗ 健康检查全部失败，看日志：$LOGFILE" >&2
  exit 1
fi

cat <<EOF

✓ 本地站点已启动
   地址：http://localhost:$PORT
   日志：$LOGFILE
   停止：bash scripts/serve-local.sh stop
EOF

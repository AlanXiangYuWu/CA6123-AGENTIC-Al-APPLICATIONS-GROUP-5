#!/usr/bin/env bash
# One-click launcher for the agentic_app stack.
# - Creates venv + installs Python deps if missing
# - Installs npm deps if missing
# - Starts FastAPI on :8000 and Vite on :5173
# - Tails both logs with prefixes
# - Ctrl+C cleanly kills both
# - Opens the browser when ready
#
# Usage:
#   ./start.sh             # full startup
#   ./start.sh --no-open   # skip opening browser
#   ./start.sh --reset     # wipe venv + node_modules + kb_store before start

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# ---- colors -----------------------------------------------------------------
if [ -t 1 ]; then
  C_RESET='\033[0m'; C_DIM='\033[2m'
  C_BLUE='\033[1;34m'; C_GREEN='\033[1;32m'; C_YEL='\033[1;33m'; C_RED='\033[1;31m'
else
  C_RESET=''; C_DIM=''; C_BLUE=''; C_GREEN=''; C_YEL=''; C_RED=''
fi
say()  { printf "${C_BLUE}[start]${C_RESET} %s\n" "$*"; }
ok()   { printf "${C_GREEN}[ ok ]${C_RESET} %s\n" "$*"; }
warn() { printf "${C_YEL}[warn]${C_RESET} %s\n" "$*"; }
err()  { printf "${C_RED}[err ]${C_RESET} %s\n" "$*" 1>&2; }

# ---- args -------------------------------------------------------------------
OPEN_BROWSER=1
RESET=0
for arg in "$@"; do
  case "$arg" in
    --no-open) OPEN_BROWSER=0 ;;
    --reset)   RESET=1 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^#//'; exit 0 ;;
    *) err "unknown arg: $arg"; exit 1 ;;
  esac
done

# ---- prereq check -----------------------------------------------------------
command -v python3 >/dev/null || { err "python3 not found"; exit 1; }
command -v node    >/dev/null || { err "node not found (install Node.js >= 18)"; exit 1; }
command -v npm     >/dev/null || { err "npm not found"; exit 1; }

if [ ! -f "$ROOT/.env" ]; then
  err ".env missing. Copy .env.example to .env and set GOOGLE_API_KEY first."
  exit 1
fi

# ---- reset (optional) -------------------------------------------------------
if [ "$RESET" -eq 1 ]; then
  warn "Resetting venv / node_modules / kb_store"
  rm -rf "$ROOT/.venv" "$ROOT/frontend/node_modules" "$ROOT/kb_store"
fi

# ---- backend setup ----------------------------------------------------------
if [ ! -d "$ROOT/.venv" ]; then
  say "Creating Python venv..."
  python3 -m venv "$ROOT/.venv"
fi

# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

if ! python -c "import fastapi, langgraph" >/dev/null 2>&1; then
  say "Installing Python deps (this may take a minute)..."
  pip install --upgrade pip --quiet
  pip install -r "$ROOT/requirements.txt" --quiet
  ok "Python deps installed"
else
  ok "Python deps already present"
fi

# ---- frontend setup ---------------------------------------------------------
if [ ! -d "$ROOT/frontend/node_modules" ]; then
  say "Installing npm deps..."
  (cd "$ROOT/frontend" && npm install --silent)
  ok "npm deps installed"
else
  ok "npm deps already present"
fi

# ---- port check -------------------------------------------------------------
for port in 8000 5173; do
  if lsof -ti:"$port" >/dev/null 2>&1; then
    warn "Port $port already in use — killing existing process"
    lsof -ti:"$port" | xargs -r kill -9 2>/dev/null || true
    sleep 1
  fi
done

# ---- launch -----------------------------------------------------------------
LOG_DIR="$ROOT/.logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
: > "$BACKEND_LOG"; : > "$FRONTEND_LOG"

say "Starting backend (FastAPI :8000)..."
( cd "$ROOT" && exec uvicorn backend.main:app \
    --host 127.0.0.1 --port 8000 --log-level info \
    >"$BACKEND_LOG" 2>&1 ) &
BACKEND_PID=$!

say "Starting frontend (Vite :5173)..."
( cd "$ROOT/frontend" && exec npm run dev -- \
    --host 127.0.0.1 --port 5173 \
    >"$FRONTEND_LOG" 2>&1 ) &
FRONTEND_PID=$!

cleanup() {
  echo
  say "Stopping services..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  ok "Stopped."
}
trap cleanup EXIT INT TERM

# ---- wait until healthy -----------------------------------------------------
say "Waiting for backend..."
for i in {1..60}; do
  if curl -sf http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    ok "Backend ready"
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    err "Backend died — see $BACKEND_LOG"
    tail -n 30 "$BACKEND_LOG" || true
    exit 1
  fi
  sleep 1
  [ "$i" -eq 60 ] && { err "Backend health check timed out"; tail -n 30 "$BACKEND_LOG"; exit 1; }
done

say "Waiting for frontend..."
for i in {1..60}; do
  if curl -sf http://127.0.0.1:5173/ >/dev/null 2>&1; then
    ok "Frontend ready"
    break
  fi
  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    err "Frontend died — see $FRONTEND_LOG"
    tail -n 30 "$FRONTEND_LOG" || true
    exit 1
  fi
  sleep 1
  [ "$i" -eq 60 ] && { err "Frontend health check timed out"; tail -n 30 "$FRONTEND_LOG"; exit 1; }
done

# ---- open browser -----------------------------------------------------------
if [ "$OPEN_BROWSER" -eq 1 ]; then
  if command -v open >/dev/null;     then open http://127.0.0.1:5173 >/dev/null 2>&1 || true
  elif command -v xdg-open >/dev/null; then xdg-open http://127.0.0.1:5173 >/dev/null 2>&1 || true
  fi
fi

# ---- banner -----------------------------------------------------------------
cat <<EOF

${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}
${C_GREEN}  agentic_app is running${C_RESET}
${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}
  ${C_BLUE}UI       ${C_RESET}  http://127.0.0.1:5173
  ${C_BLUE}API docs ${C_RESET}  http://127.0.0.1:8000/docs
  ${C_BLUE}Logs     ${C_RESET}  $LOG_DIR/{backend,frontend}.log

  Press ${C_YEL}Ctrl+C${C_RESET} to stop both.
${C_DIM}Streaming combined logs below...${C_RESET}

EOF

# ---- combined log tail ------------------------------------------------------
tail -F -n 0 "$BACKEND_LOG" 2>/dev/null | sed -u "s/^/${C_BLUE}[backend]${C_RESET} /" &
TAIL_BE=$!
tail -F -n 0 "$FRONTEND_LOG" 2>/dev/null | sed -u "s/^/${C_GREEN}[frontend]${C_RESET} /" &
TAIL_FE=$!

trap 'kill $TAIL_BE $TAIL_FE 2>/dev/null || true; cleanup' EXIT INT TERM

# Block on backend; if it dies, exit (cleanup handles the rest).
wait "$BACKEND_PID"

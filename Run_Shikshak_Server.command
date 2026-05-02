#!/bin/zsh

cd "$(dirname "$0")" || exit 1

HOST="127.0.0.1"
PORT="5001"
URL="http://${HOST}:${PORT}"

clear
echo "Starting Shikshak Nigrani & Analysis System..."
echo

if lsof -nP -iTCP:${PORT} -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Server is already running on ${URL}"
  open "${URL}"
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 was not found. Please install Python 3 and try again."
  read -r "?Press Enter to close..."
  exit 1
fi

(
  sleep 2
  open "${URL}"
) &

echo "Opening ${URL}"
echo "Keep this Terminal window open while using the app."
echo "Press Ctrl+C here to stop the server."
echo

HOST="${HOST}" PORT="${PORT}" python3 app.py

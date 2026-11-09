#!/usr/bin/env bash
# 동작 확인: bash .refactor/check.sh  (하나라도 실패하면 실패)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/Scripts/python
[ -x "$PY" ] || PY=.venv/bin/python
export PYTHONUTF8=1

echo "[1/4] 문법 검사";      "$PY" -m compileall -q -x '[\\/]\.venv[\\/]' .
echo "[2/4] 이름·import 검사"; "$PY" -m ruff check --select F --exclude .venv,.refactor,data,results .
echo "[3/4] 모듈 불러오기"
for f in *.py; do
  "$PY" -c "import importlib, sys; importlib.import_module(sys.argv[1])" "${f%.py}"
done
echo "[4/4] 테스트";        "$PY" -m pytest -q
echo "확인 통과"

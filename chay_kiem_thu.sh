#!/usr/bin/env bash
# Chạy 24 ca kiểm thử + tự xuất báo cáo (macOS / Linux) bằng MỘT lệnh.
#   ./chay_kiem_thu.sh                 mặc định lặp 20 lần/ca, xong tự mở báo cáo HTML
#   ./chay_kiem_thu.sh --lap 50        đo kỹ hơn
#   ./chay_kiem_thu.sh --dinh-dang html,docx
# Lần đầu: tự tạo môi trường ảo .venv và cài thư viện (cần Internet).
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  PY=""
  for c in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
      PY="$c"; break
    fi
  done
  if [ -z "$PY" ]; then
    echo "!! Cần Python 3.10 trở lên. macOS: brew install python@3.12  (hoặc tải tại python.org)"; exit 2
  fi
  echo ">> Tạo môi trường ảo .venv bằng $PY"
  "$PY" -m venv .venv
  .venv/bin/python -m pip install -q --upgrade pip
fi

echo ">> Kiểm tra thư viện"
.venv/bin/python -m pip install -q -r requirements.txt -r requirements-bao-cao.txt

.venv/bin/python xuat_bao_cao.py --chay --mo "$@"

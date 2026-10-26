#!/bin/bash
# Chạy các thí nghiệm 2–6 theo thứ tự (sau exp1_tuning, exp1b, finalize_exp1, exp1c). Mỗi bước ghi log riêng; một bước lỗi không chặn bước sau.
cd "$(dirname "$0")/.."
LOG=${LOG:-/tmp}
for s in "$@"; do
  echo "== $s $(date +%H:%M:%S)"; python3 experiments/$s.py > $LOG/$s.log 2>&1 || echo "LỖI ở $s (xem $LOG/$s.log)"
done
echo ALL_DONE > $LOG/exp_all.done

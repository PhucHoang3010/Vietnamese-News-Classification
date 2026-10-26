#!/bin/bash
# Chạy các thí nghiệm còn lại theo thứ tự (sau exp1_tuning.py). Mỗi bước ghi log riêng; một bước lỗi không chặn bước sau.
cd "$(dirname "$0")/.."
for s in exp1b_extend_edges finalize_exp1 exp2_ablation exp3_stability exp4_learning_curve exp5_calibration exp6_errors; do
  echo "== $s $(date +%H:%M:%S)"; python3 experiments/$s.py > /tmp/$s.log 2>&1 || echo "LỖI ở $s (xem /tmp/$s.log)"
done
echo ALL_DONE > /tmp/exp_all.done

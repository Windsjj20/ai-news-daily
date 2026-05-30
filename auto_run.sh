#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=== AI Daily 自动采集开始: $(date) ==="

# 采集 + 生成
python3 run.py run

# 推送到 GitHub
git add -A
git commit -m "daily update $(date +%Y-%m-%d)" || true
git push origin main 2>&1

echo "=== 完成: $(date) ==="

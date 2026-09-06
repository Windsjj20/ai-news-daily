#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=== AI Daily 自动采集开始: $(date) ==="

# 采集 + 生成（失败则 set -e 直接终止，不推送半成品）
python3 run.py run

# 若无变更则跳过推送（cron 重复触发场景）
if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
  echo "无变更，跳过 commit/push"
  exit 0
fi

# 推送到 GitHub —— push 失败必须显式暴露，禁止静默吞掉
git add -A
git commit -m "daily update $(date +%Y-%m-%d)" || true
if ! git push origin main; then
  echo "❌❌❌ GIT PUSH 失败！本地已 commit 但未同步到远程（origin/main）"
  echo "   远程站点（Cloudflare Pages 等）不会更新。请立即手动重试："
  echo "   cd $(pwd) && git push origin main"
  echo "   或用：  git status 核对本地领先 origin/main 的 commit 数"
  exit 1
fi

# push 成功后再校验一次，确认本地与远程一致
git fetch origin main --quiet 2>/dev/null || true
if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
  echo "⚠️ push 返回成功但本地仍领先远程，需人工检查"
  exit 1
fi

echo "=== 完成: $(date)，已同步 origin/main ==="

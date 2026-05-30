#!/usr/bin/env python3
"""AI Daily - 全流程运行脚本"""
import sys, os, json
from datetime import datetime

BASE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE, "src"))

from fetch import fetch_all, save, clean_history
from build import build_site
from tag import tag_with_ai

def run():
    """完整运行一次：采集 → AI打标签 → 排序 → 生成网站"""
    print(f"🚀 AI Daily 开始运行 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("=" * 40)
    
    # 第 1 步：采集
    print("\n🕷️ 第 1 步：采集资讯")
    items = fetch_all()
    history = save(items)
    
    # 第 2 步：AI 打标签
    print("\n🏷️ 第 2 步：AI 打标签")
    history = tag_with_ai(history)
    # 写回
    import json
    hist_file = os.path.join(BASE, "data", "history.json")
    with open(hist_file, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    # 第 3 步：生成网站（含 AI 排序）
    print("\n🏗️ 第 3 步：生成网站")
    ok = build_site()
    
    if ok:
        print("\n✅ 运行完毕！")
        print(f"   网站输出: projects/ai-news-daily/output/")
        print(f"   共 {len(history)} 篇文章")
    return ok

def deploy():
    """部署到 Gitee Pages"""
    import subprocess
    output_dir = os.path.join(BASE, "output")
    
    # 检查是否已初始化为 Gitee 仓库
    gitee_dir = os.path.join(output_dir, ".git")
    if not os.path.exists(gitee_dir):
        print("⚠️ 尚未初始化 Gitee 仓库，请先配置：")
        print(f"   cd {output_dir}")
        print("   git init")
        print("   git remote add origin https://gitee.com/windsjj/ai-news.git")
        print("   git add . && git commit -m 'initial' && git push -u origin master")
        print("\n   然后去 Gitee → 仓库 → 服务 → Gitee Pages 开启 Pages 服务")
        return False
    
    # 部署
    result = subprocess.run(
        ["git", "-C", output_dir, "add", "-A"],
        capture_output=True, text=True
    )
    result = subprocess.run(
        ["git", "-C", output_dir, "commit", "-m", f"update {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
        capture_output=True, text=True
    )
    result = subprocess.run(
        ["git", "-C", output_dir, "push"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"✅ 已部署到 Gitee Pages!")
        site_url = f"https://windsjj.gitee.io/ai-news"
        print(f"   🌐 {site_url}")
        return site_url
    else:
        print(f"❌ 部署失败: {result.stderr}")
        return False

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        run()
    elif cmd == "deploy":
        deploy()
    elif cmd == "clean":
        if len(sys.argv) < 3:
            print("用法: python3 run.py clean YYYY-MM-DD")
            sys.exit(1)
        removed = clean_history(sys.argv[2])
        print(f"🧹 已清理 {removed} 条旧数据")
    else:
        print(f"用法: python3 run.py [run|deploy|clean YYYY-MM-DD]")

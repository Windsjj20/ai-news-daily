#!/usr/bin/env python3
"""AI Daily - 网站生成模块"""
import json, os, shutil, re
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

def load_history() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE) as f:
        return json.load(f)

def ai_sort(items: list[dict]) -> list[dict]:
    if not items:
        return items
    items.sort(key=lambda x: x.get("pub_date") or x.get("fetched_at", ""), reverse=True)
    def sort_score(item):
        score = 0
        if item.get("image"): score += 3
        if "官方" in item.get("tags", []): score += 2
        if "社区热议" in item.get("tags", []): score += 1
        if "模型发布" in item.get("tags", []): score += 1
        return score
    items.sort(key=lambda x: (
        sort_score(x) + (0 if x.get("pub_date") else -10)
    ), reverse=True)
    return items

def build_site():
    history = load_history()
    if not history:
        print("❌ 没有数据，请先运行 fetch.py")
        return

    print(f"📦 共 {len(history)} 篇文章，开始生成网站...")

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    sorted_articles = ai_sort(history)

    # 写入 data.json
    data_json = json.dumps(sorted_articles, ensure_ascii=False)
    with open(os.path.join(OUTPUT_DIR, "data.json"), "w", encoding="utf-8") as f:
        f.write(data_json)
    print(f"📝 data.json: {len(data_json)} bytes")

    # 生成首页（只这一个页面）
    with open(os.path.join(TEMPLATE_DIR, "index.html")) as f:
        index_tpl = f.read()
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_tpl)
    print(f"🏠 index.html 已生成（直接跳转原文，无需详情页）")

    # 写入 version
    today = datetime.now().strftime("%Y-%m-%d")
    today_articles = [a for a in sorted_articles if a.get("date") == today]
    version_info = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_articles": len(history),
        "today_articles": len(today_articles),
    }
    with open(os.path.join(OUTPUT_DIR, "version.json"), "w") as f:
        json.dump(version_info, f)

    print(f"✅ 网站生成完毕 → {OUTPUT_DIR}/")
    print(f"   📊 共 {len(history)} 篇文章，今日 {len(today_articles)} 篇")
    return True

def clean_site(before_date: str) -> int:
    import sys
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from fetch import clean_history
    return clean_history(before_date)

if __name__ == "__main__":
    build_site()

#!/usr/bin/env python3
"""AI Daily - AI 自动打标签模块（纯标准库）"""
import json, os, time, re
import urllib.request, urllib.error

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

KNOWN_TAGS = [
    "模型发布", "开源", "融资", "收购", "政策法规", "AI安全",
    "算力", "硬件", "应用落地", "创业", "社区热议", "深度",
    "官方", "产业", "国产替代", "科技", "学术",
]

def tag_with_ai(articles: list[dict]) -> list[dict]:
    if not articles:
        return articles

    to_tag = [a for a in articles if not a.get("tags") or
              set(a.get("tags", [])) <= set(["产业","国产替代","社区热议","创业","融资","科技","深度","官方","算力","硬件"])]

    if not to_tag:
        print(f"  AI标签: 无需更新（{len(articles)} 篇已有标签）")
        return articles

    print(f"  AI标签: 处理 {len(to_tag)} 篇...")

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    has_api = bool(api_key)

    batch_size = 5
    tagged_count = 0

    for i in range(0, len(to_tag), batch_size):
        batch = to_tag[i:i+batch_size]

        if has_api:
            success = _call_deepseek_api(batch, api_key)
            if success:
                tagged_count += len([a for a in batch if a.get("tags")])
                print(f"    ✓ 批次 {i//batch_size + 1}: 标记 {len(batch)} 篇")
            else:
                _tag_batch_default(batch)
                print(f"    ⚠️ 批次 {i//batch_size + 1} API 失败，用默认标签")
        else:
            _tag_batch_default(batch)
            print(f"    ⚠️ 无 API Key，用默认标签")

        time.sleep(0.3)

    print(f"  AI标签完成: 共处理 {len(to_tag)} 篇")
    return articles

def _call_deepseek_api(batch, api_key):
    """调用 DeepSeek API 打标签"""
    articles_text = "\n---\n".join([
        f"标题: {a.get('title','')}\n摘要: {a.get('summary','')[:200]}\n来源: {a.get('source','')}"
        for a in batch
    ])

    prompt = f"""你是一个AI资讯标签专家。请为以下每篇文章从标签库中选择最匹配的1-3个标签。

标签库：{', '.join(KNOWN_TAGS)}

如果都不匹配，选最接近的，不超过3个。
格式要求：每行输出 [序号] 标签1, 标签2
例如：
[1] 模型发布, 开源
[2] 融资, 创业

文章列表：
{articles_text}"""

    data = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.1,
    }).encode()

    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
            text = result["choices"][0]["message"]["content"]

        for line in text.strip().split("\n"):
            line = line.strip()
            if not line or "[" not in line:
                continue
            match = re.match(r'\[(\d+)\]\s*(.*)', line)
            if match:
                idx = int(match.group(1)) - 1
                tags_text = match.group(2)
                new_tags = [t.strip() for t in tags_text.split(",") if t.strip()]
                new_tags = [t for t in new_tags if t in KNOWN_TAGS]
                if new_tags and idx < len(batch):
                    batch[idx]["tags"] = list(set(batch[idx].get("tags", []) + new_tags))
        return True
    except Exception as e:
        print(f"    API 调用失败: {e}")
        return False

def _tag_batch_default(batch):
    """无 API 时的后备标签"""
    for a in batch:
        src = a.get("source", "")
        existing = a.get("tags", [])
        if "机器之心" in src:
            if "深度" not in existing:
                a["tags"] = existing + ["深度"]
        elif "量子位" in src:
            if "科技" not in existing:
                a["tags"] = existing + ["科技"]
        elif "新智元" in src:
            if "产业" not in existing:
                a["tags"] = existing + ["产业"]
        elif "Hacker News" in src:
            if "社区热议" not in existing:
                a["tags"] = existing + ["社区热议"]
        elif "MIT" in src:
            if "深度" not in existing:
                a["tags"] = existing + ["深度"]
        elif not existing:
            a["tags"] = ["科技"]

def run():
    if not os.path.exists(HISTORY_FILE):
        print("❌ history.json 不存在，先运行 fetch.py")
        return
    with open(HISTORY_FILE) as f:
        history = json.load(f)

    print(f"📦 共 {len(history)} 篇文章，开始 AI 打标签...")
    tagged = tag_with_ai(history)

    with open(HISTORY_FILE, "w") as f:
        json.dump(tagged, f, ensure_ascii=False, indent=2)
    print("✅ AI 标签处理完毕")

if __name__ == "__main__":
    run()

#!/usr/bin/env python3
"""AI Daily - 资讯采集模块（纯标准库，无外部依赖）"""
import json, os, time, re, hashlib
import xml.etree.ElementTree as ET
import urllib.request, urllib.error
from datetime import datetime
from typing import Optional

# Ensure sources can be imported
import sys
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
from sources import SOURCES

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

def clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def fetch_url(url: str, timeout=15) -> Optional[str]:
    """带 User-Agent 的 HTTP GET"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "AI-News-Daily/1.0",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None

def parse_rss(xml_text: str, source, max_items=10) -> list[dict]:
    """解析 RSS/Atom XML 为文章列表"""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    
    # RSS 2.0 格式
    entries = []
    if root.tag == "rss":
        channel = root.find("channel")
        if channel is not None:
            entries = channel.findall("item")
    # Atom 格式
    elif root.tag.endswith("feed"):
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        if not entries:
            # 尝试命名空间自动探测
            entries = root.findall(".//entry")
    
    for entry in entries[:max_items]:
        title = _tag_text(entry, "title")
        if not title:
            continue
        
        link = _tag_text(entry, "link") or ""
        # Atom 的 link 在 href 属性里
        if not link.startswith("http"):
            link = entry.findtext(".//{http://www.w3.org/2005/Atom}link/@href") or ""
            if not link.startswith("http"):
                for ln in entry.findall("link"):
                    href = ln.get("href", "")
                    if href:
                        link = href
                        break
        
        summary = _tag_text(entry, "description") or _tag_text(entry, "summary") or ""
        summary = clean_html(summary)[:300]
        
        pub_date = _tag_text(entry, "pubDate") or _tag_text(entry, "published") or _tag_text(entry, "updated") or ""
        
        # 提取图片（enclosure / media:content）
        image = ""
        enc = entry.find("enclosure")
        if enc is not None and enc.get("type", "").startswith("image"):
            image = enc.get("url", "")
        if not image:
            # 从描述里提取第一张图片
            desc = entry.find("description")
            if desc is not None and desc.text:
                m = re.search(r'<img[^>]+src=["\']([^"\']+)', desc.text)
                if m:
                    image = m.group(1)
        
        items.append({
            "id": hashlib.md5(link.encode()).hexdigest()[:12],
            "title": title,
            "link": link,
            "summary": summary,
            "source": source.name,
            "region": source.region,
            "lang": source.lang,
            "tags": list(source.tags),
            "image": image,
            "pub_date": pub_date,
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
    
    return items

def _tag_text(parent, tag):
    """安全获取标签文本"""
    el = parent.find(tag)
    if el is not None and el.text:
        return el.text.strip()
    return ""

def fetch_rss(source, max_items=10) -> list[dict]:
    """抓取单个 RSS 源"""
    xml = fetch_url(source.feed_url)
    if not xml:
        print(f"  ❌ {source.name}: 请求失败")
        return []
    items = parse_rss(xml, source, max_items)
    print(f"    ✓ {source.name}: {len(items)} 篇")
    return items

def fetch_wp_json(source, max_items=10) -> list[dict]:
    """通过 WordPress REST API 采集（RSS 失效时的后备方案）"""
    import json
    api_url = source.url.rstrip("/") + "/wp-json/wp/v2/posts?per_page=" + str(max_items) + "&_embed"
    html = fetch_url(api_url)
    if not html:
        print(f"  ❌ {source.name}: API 请求失败")
        return []
    try:
        posts = json.loads(html)
    except json.JSONDecodeError:
        print(f"  ❌ {source.name}: JSON 解析失败")
        return []
    if not isinstance(posts, list):
        print(f"  ❌ {source.name}: 非预期返回格式")
        return []
    
    items = []
    for p in posts:
        title = p.get("title", {}).get("rendered", "") or ""
        title = clean_html(title).strip()
        if not title:
            continue
        link = p.get("link", "") or ""
        summary = p.get("excerpt", {}).get("rendered", "") or ""
        summary = clean_html(summary)[:300]
        date = (p.get("date") or "")[:10]
        
        # 尝试取特色图片
        image = ""
        embedded = p.get("_embed", {})
        wpmedia = embedded.get("wp:featuredmedia", [])
        if wpmedia:
            media_urls = wpmedia[0].get("source_url", "") or \
                         wpmedia[0].get("media_details", {}).get("sizes", {}).get("medium", {}).get("source_url", "") or ""
            if media_urls:
                image = media_urls
        
        item_id = hashlib.md5(link.encode()).hexdigest()[:12]
        items.append({
            "id": item_id,
            "title": title,
            "link": link,
            "summary": summary,
            "source": source.name,
            "region": source.region,
            "lang": source.lang,
            "tags": list(source.tags),
            "image": image,
            "pub_date": date,
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
    
    print(f"    ✓ {source.name}: {len(items)} 篇 (WP-API)")
    return items


def fetch_source(source, max_items=10) -> list[dict]:
    """尝试 RSS 采集，失败则回退到 WordPress REST API"""
    items = fetch_rss(source, max_items)
    if items:
        return items
    # RSS 失败，尝试 WP REST API
    items = fetch_wp_json(source, max_items)
    return items


def fetch_all() -> list[dict]:
    all_items = []
    print("🕷️ 开始采集...")
    for src in SOURCES:
        print(f"  → {src.name}")
        items = fetch_source(src)
        all_items.extend(items)
        time.sleep(0.5)
    
    # 去重
    seen = set()
    unique = []
    for item in all_items:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)
    
    print(f"📊 共采集 {len(all_items)} 篇，去重后 {len(unique)} 篇")
    return unique

def save(items: list[dict]) -> list[dict]:
    hist_file = os.path.join(DATA_DIR, "history.json")
    today = datetime.now().strftime("%Y-%m-%d")
    
    history = []
    if os.path.exists(hist_file):
        with open(hist_file) as f:
            history = json.load(f)
    
    existing_ids = {item["id"] for item in history}
    new_count = 0
    for item in items:
        if item["id"] not in existing_ids:
            item["date"] = today
            history.append(item)
            existing_ids.add(item["id"])
            new_count += 1
    
    history.sort(key=lambda x: x.get("pub_date") or x.get("fetched_at", ""), reverse=True)
    with open(hist_file, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    print(f"💾 新增 {new_count} 篇到历史（共 {len(history)} 篇）")
    return history

def clean_history(before_date: str) -> int:
    hist_file = os.path.join(DATA_DIR, "history.json")
    if not os.path.exists(hist_file):
        return 0
    with open(hist_file) as f:
        history = json.load(f)
    
    kept = [item for item in history if item.get("date", "") >= before_date]
    removed = len(history) - len(kept)
    
    with open(hist_file, "w") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)
    return removed

if __name__ == "__main__":
    items = fetch_all()
    save(items)

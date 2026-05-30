"""AI 资讯源配置"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Source:
    name: str
    url: str           # 网站首页
    feed_url: str      # RSS/feed 地址
    region: str        # "cn" 或 "global"
    lang: str          # "zh" 或 "en"
    tags: list[str]    # 默认标签

SOURCES = [
    # ===== 国际资讯 =====
    Source("Hacker News", "https://news.ycombinator.com",
           "https://hnrss.org/frontpage", "global", "en",
           ["社区热议", "创业"]),
    Source("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/",
           "https://techcrunch.com/category/artificial-intelligence/feed/", "global", "en",
           ["创业", "融资"]),
    Source("The Verge AI", "https://www.theverge.com/ai-artificial-intelligence",
           "https://www.theverge.com/ai-artificial-intelligence/rss.xml", "global", "en",
           ["科技"]),
    Source("Hugging Face Blog", "https://huggingface.co/blog",
           "https://huggingface.co/blog/feed.xml", "global", "en",
           ["开源", "模型发布"]),
    Source("MIT Tech Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/",
           "https://www.technologyreview.com/topic/artificial-intelligence/feed/", "global", "en",
           ["深度"]),

    # ===== 国内资讯 =====
    Source("机器之心", "https://www.jiqizhixin.com",
           "https://www.jiqizhixin.com/rss", "cn", "zh",
           []),
    Source("量子位", "https://www.qbitai.com",
           "https://www.qbitai.com/feed", "cn", "zh",
           []),
    Source("新智元", "https://aiera.com.cn",
           "https://aiera.com.cn/feed.xml", "cn", "zh",
           ["产业", "国产替代"]),

    # ===== 官方/一手 =====
    Source("OpenAI Blog", "https://openai.com/blog",
           "https://openai.com/blog/feed.xml", "global", "en",
           ["官方"]),
    Source("Google AI Blog", "https://ai.googleblog.com",
           "https://ai.googleblog.com/feeds/posts/default", "global", "en",
           ["官方"]),
    Source("Anthropic News", "https://www.anthropic.com/news",
           "https://www.anthropic.com/news/feed.xml", "global", "en",
           ["官方"]),
    Source("英伟达 AI Blog", "https://blogs.nvidia.com/",
           "https://blogs.nvidia.com/feed/", "global", "en",
           ["算力", "硬件"]),
]

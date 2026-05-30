# AI Daily - AI 资讯日报

每日自动采集 AI 资讯 → AI 排序 → 生成静态网站 → 部署到 GitHub Pages

## 技术栈

- Python 3：采集 + 处理 + 生成
- GitHub Pages：免费托管
- DeepSeek API：AI 摘要 + 排序

## 使用方式

```bash
# 安装依赖
pip install requests feedparser

# 运行一次（测试）
python3 src/fetch.py
python3 src/build.py

# 生成的网站在 output/ 目录
```

## 项目结构

```
ai-news-daily/
├── src/
│   ├── fetch.py        # 采集所有源
│   ├── sources.py      # 源配置
│   ├── build.py        # 生成 HTML 网站
│   └── templates/      # HTML 模板
├── output/             # 生成的静态网站
├── data/               # 缓存/数据
└── .github/            # GitHub Actions（后续）
```

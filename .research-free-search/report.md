# 免费联网搜索方案研究报告

> 研究日期：2026年3月12日  
> 研究目标：收集所有可用于OpenClaw/AI Agent的免费联网搜索方法

---

## 目录

1. [执行摘要](#执行摘要)
2. [免费搜索API](#免费搜索api)
3. [网页抓取方案](#网页抓取方案)
4. [现有OpenClaw Skills分析](#现有openclaw-skills分析)
5. [其他AI Agent项目实现](#其他ai-agent项目实现)
6. [推荐方案](#推荐方案)
7. [结论与建议](#结论与建议)

---

## 执行摘要

本报告系统研究了可用于AI Agent的免费联网搜索方案，涵盖免费搜索API、网页抓取技术、OpenClaw现有实现以及其他开源项目的方案。研究发现：

| 方案类型 | 数量 | 推荐度 |
|---------|------|--------|
| 免费搜索API | 8+ | ⭐⭐⭐⭐ |
| 网页抓取 | 4+ | ⭐⭐⭐ |
| 自建搜索 | 2 | ⭐⭐⭐⭐⭐ |

**最推荐方案**：DuckDuckGo Search (ddgs) + SearXNG自建搜索 组合方案

---

## 免费搜索API

### 1. DuckDuckGo Search (ddgs) ⭐ **强烈推荐**

| 属性 | 详情 |
|------|------|
| **费用** | 完全免费，无需API Key |
| **实现难度** | ⭐⭐ 简单 |
| **支持后端** | Bing, Brave, DuckDuckGo, Google, Yandex等 |
| **搜索类型** | 文本、图片、视频、新闻、图书 |
| **Python版本** | >= 3.10 |

#### 代码示例

```bash
# 安装
pip install -U duckduckgo-search
```

```python
from duckduckgo_search import DDGS

# 基础文本搜索
with DDGS() as ddgs:
    results = list(ddgs.text("Python tutorial", max_results=5))
    for r in results:
        print(f"标题: {r['title']}")
        print(f"链接: {r['href']}")
        print(f"摘要: {r['body']}")
        print('---')

# 新闻搜索
with DDGS() as ddgs:
    results = list(ddgs.news("AI breakthrough", max_results=5))

# 图片搜索
with DDGS() as ddgs:
    results = list(ddgs.images("mountain landscape", max_results=5))

# 视频搜索
with DDGS() as ddgs:
    results = list(ddgs.videos("Python tutorial", max_results=5))
```

#### 优点
- ✅ 完全免费，无需注册
- ✅ 隐私友好，不追踪用户
- ✅ 多后端支持（自动故障转移）
- ✅ 支持代理、时间过滤、区域设置

#### 缺点
- ⚠️ 可能遇到速率限制（连续大量请求时）
- ⚠️ 结果质量略低于商业API

---

### 2. SearXNG 自建搜索 ⭐ **强烈推荐**

| 属性 | 详情 |
|------|------|
| **费用** | 完全免费开源 |
| **实现难度** | ⭐⭐⭐⭐ 中等（需要Docker/服务器） |
| **聚合引擎** | 70+ 搜索引擎 |
| **隐私保护** | 不追踪、不记录 |
| **部署方式** | Docker / 源码安装 |

#### Docker部署

```bash
# 创建工作目录
mkdir my-searxng && cd my-searxng
mkdir config data

# 拉取镜像
docker pull searxng/searxng

# 运行容器
export PORT=8888
docker run --name searxng --replace -d \
    -p ${PORT}:8080 \
    -v "${PWD}/config:/etc/searxng" \
    -v "${PWD}/data:/var/cache/searxng" \
    -e "BASE_URL=http://localhost:$PORT/" \
    -e "INSTANCE_NAME=my-searxng" \
    searxng/searxng
```

#### Python调用

```python
import requests

def searxng_search(query, instance_url="http://localhost:8888"):
    params = {
        'q': query,
        'format': 'json',
        'language': 'zh-CN',
        'safesearch': 0
    }
    response = requests.get(f"{instance_url}/search", params=params)
    return response.json()

# 使用
results = searxng_search("Python AI agents")
for result in results.get('results', []):
    print(f"{result['title']}: {result['url']}")
```

#### 优点
- ✅ 完全掌控数据源
- ✅ 聚合70+搜索引擎
- ✅ 最高隐私保护
- ✅ 可自定义配置
- ✅ 无API限制

#### 缺点
- ⚠️ 需要服务器资源
- ⚠️ 初始配置较复杂
- ⚠️ 需要维护更新

---

### 3. Brave Search API

| 属性 | 详情 |
|------|------|
| **免费额度** | ~1,000 查询/月 |
| **付费价格** | $5-9/1,000 请求 |
| **实现难度** | ⭐⭐ 简单 |
| **独立索引** | 是（30B+ 页面） |

#### 代码示例

```python
import requests

BRAVE_API_KEY = "your_api_key"

def brave_search(query):
    headers = {"X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": query, "count": 10}
    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers=headers,
        params=params
    )
    return response.json()
```

#### 优点
- ✅ 独立搜索索引
- ✅ SOC 2 Type II 认证
- ✅ 无用户追踪
- ✅ 响应快速

#### 缺点
- ⚠️ 需要API Key
- ⚠️ 免费额度有限

---

### 4. Google Custom Search JSON API

| 属性 | 详情 |
|------|------|
| **免费额度** | 100 查询/天 |
| **付费价格** | $5/1,000 查询 |
| **实现难度** | ⭐⭐ 简单 |
| **上限** | 10,000 查询/天 |

#### 代码示例

```python
from googleapiclient.discovery import build

API_KEY = "your_api_key"
SEARCH_ENGINE_ID = "your_search_engine_id"

def google_custom_search(query):
    service = build("customsearch", "v1", developerKey=API_KEY)
    result = service.cse().list(q=query, cx=SEARCH_ENGINE_ID).execute()
    return result.get('items', [])
```

#### 优点
- ✅ Google搜索质量
- ✅ 稳定可靠
- ✅ 丰富的过滤选项

#### 缺点
- ⚠️ 免费额度极低（100/天）
- ⚠️ 需要Google Cloud项目
- ⚠️ 需要绑定支付方式

---

### 5. Bing Web Search API ⚠️ **已停止服务**

| 属性 | 详情 |
|------|------|
| **状态** | 已于2025年8月11日停止服务 |
| **替代方案** | Azure AI Agents Grounding |
| **替代价格** | $35/1,000 查询 |

> ⚠️ **重要提示**：Microsoft已于2025年8月11日完全停止Bing Search API服务，包括免费和付费层级。开发者需要迁移到其他替代方案。

---

### 6. Tavily Search API

| 属性 | 详情 |
|------|------|
| **免费额度** | 1,000 credits/月 |
| **付费价格** | $0.008/credit |
| **特点** | AI优化结果 |
| **LangChain** | 原生支持 |

#### 代码示例

```python
from langchain_community.tools import TavilySearchResults

tool = TavilySearchResults(max_results=5)
results = tool.invoke({"query": "AI agents 2025"})
```

#### 优点
- ✅ 专为AI Agent优化
- ✅ 结果包含相关性评分
- ✅ 可直接用于RAG

#### 缺点
- ⚠️ 需要API Key
- ⚠️ 免费额度有限

---

### 7. SerpAPI

| 属性 | 详情 |
|------|------|
| **免费额度** | 100 查询/月 |
| **付费价格** | $75/月起 |
| **支持引擎** | Google, Bing, DuckDuckGo等25+ |

#### 代码示例

```python
from serpapi import GoogleSearch

params = {
    "q": "Python programming",
    "api_key": "your_api_key",
    "engine": "google"
}
search = GoogleSearch(params)
results = search.get_dict()
```

#### 优点
- ✅ 多引擎支持
- ✅ 结构化SERP数据
- ✅ 实时结果

#### 缺点
- ⚠️ 免费额度少
- ⚠️ 付费较贵

---

### 8. Exa AI Search

| 属性 | 详情 |
|------|------|
| **免费额度** | 1,000 credits |
| **特点** | 语义搜索（嵌入向量） |
| **最适合** | RAG工作流 |

#### 代码示例

```python
from exa_py import Exa

exa = Exa("your_api_key")
results = exa.search("AI safety research", num_results=10)
```

#### 优点
- ✅ 语义理解能力强
- ✅ Find Similar功能
- ✅ 适合研究工具

#### 缺点
- ⚠️ 价格较高
- ⚠️ 非传统关键词搜索

---

## 网页抓取方案

### 1. Playwright ⭐ **推荐**

| 属性 | 详情 |
|------|------|
| **开发方** | Microsoft |
| **支持语言** | Python, Java, C#, Node.js |
| **支持浏览器** | Chromium, Firefox, WebKit |
| **特点** | 内置隐身模式，绕过反爬 |

#### 代码示例

```python
from playwright.sync_api import sync_playwright

def playwright_search(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page.goto(url)
        content = page.content()
        browser.close()
        return content
```

#### 反爬技术

```python
# 使用 Playwright Stealth
from playwright_stealth import stealth_sync

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    stealth_sync(page)  # 应用隐身补丁
    page.goto("https://example.com")
```

#### 优点
- ✅ 现代Web应用支持好
- ✅ 自动等待元素加载
- ✅ 内置反检测能力
- ✅ 多浏览器支持

#### 缺点
- ⚠️ 内存占用较高
- ⚠️ 启动速度较慢

---

### 2. Selenium

| 属性 | 详情 |
|------|------|
| **特点** | 最广泛使用的自动化框架 |
| **支持语言** | Python, Java, C#, Ruby等 |
| **GitHub Stars** | 28.6k |

#### 代码示例

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)
driver.get("https://example.com")
content = driver.page_source
driver.quit()
```

#### 反爬增强：Undetected ChromeDriver

```python
import undetected_chromedriver as uc

driver = uc.Chrome(headless=True)
driver.get("https://example.com")
```

#### 优点
- ✅ 生态系统完善
- ✅ 文档丰富
- ✅ 社区支持好

#### 缺点
- ⚠️ 易被检测（需配合stealth插件）
- ⚠️ 执行速度较慢
- ⚠️ 资源占用较高

---

### 3. 直接HTTP请求 + 解析

| 属性 | 详情 |
|------|------|
| **库推荐** | requests + BeautifulSoup / lxml |
| **适用场景** | 静态页面、简单爬取 |
| **性能** | ⭐⭐⭐⭐⭐ 最高 |

#### 代码示例

```python
import requests
from bs4 import BeautifulSoup

def simple_scrape(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 提取标题和所有链接
    title = soup.find('h1').text if soup.find('h1') else ""
    links = [a['href'] for a in soup.find_all('a', href=True)]
    
    return {"title": title, "links": links}
```

#### 优点
- ✅ 速度最快
- ✅ 资源占用最低
- ✅ 实现简单

#### 缺点
- ⚠️ 无法执行JavaScript
- ⚠️ 现代SPA网站不兼容

---

### 4. Requests-HTML

| 属性 | 详情 |
|------|------|
| **特点** | requests作者开发的整合库 |
| **功能** | HTTP请求 + 解析一体化 |
| **JS支持** | 内置（通过Pyppeteer） |

#### 代码示例

```python
from requests_html import HTMLSession

session = HTMLSession()
r = session.get('https://python.org/')

# CSS选择器查找
intro = r.html.find('#intro', first=True)
print(intro.text)

# 获取所有链接
for link in r.html.links:
    print(link)

# 执行JavaScript
r.html.render()
```

#### 优点
- ✅ 一体化解决方案
- ✅ 语法简洁
- ✅ 支持JavaScript渲染

#### 缺点
- ⚠️ 项目维护不活跃
- ⚠️ 依赖较多

---

## 绕过反爬的技术

### 1. 请求头伪装

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}
```

### 2. 代理轮换

```python
import random

proxies = [
    "http://proxy1.com:8080",
    "http://proxy2.com:8080",
]

def get_proxy():
    return {"http": random.choice(proxies), "https": random.choice(proxies)}

response = requests.get(url, proxies=get_proxy())
```

### 3. 请求频率控制

```python
import time
import random

def random_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

# 每次请求后随机延迟
for url in urls:
    scrape(url)
    random_delay()
```

### 4. Cookie和Session管理

```python
import requests

session = requests.Session()

# 先访问主页获取cookie
session.get("https://example.com")

# 后续请求自动携带cookie
response = session.get("https://example.com/data")
```

---

## 现有OpenClaw Skills分析

### 1. research-orchestrator (研究编排器)

**位置**: `/root/.openclaw/skills/research-orchestrator/`

**功能**:
- 多源研究编排
- 交叉验证
- 洞察提取
- 自动报告生成

**使用方式**:
```bash
./scripts/research.sh "quantum computing breakthroughs 2024"
```

**依赖工具**:
- `web_search` - OpenClaw内置搜索
- `kimi_search` - Kimi搜索集成
- `web_fetch` - 网页抓取
- `browser` - 浏览器自动化

### 2. advanced-research-orchestrator (高级研究编排器)

**位置**: `/root/.openclaw/skills/advanced-research-orchestrator/`

**功能**:
- 基于Knowledge-Extractor框架
- 四维评估（相关性/权威性/时效性/可信度）
- 知识图谱存储
- DeepResearchAgent工作流

**核心架构**:
```
Schedule Trigger → Multi-Source Ingestion → AI Validation → KAG Storage
```

### 3. OpenClaw内置搜索工具

| 工具 | 类型 | 费用 |
|------|------|------|
| `web_search` | Brave Search API | 需要API Key |
| `kimi_search` | Kimi集成搜索 | 免费（通过Kimi） |
| `web_fetch` | 直接网页抓取 | 免费 |
| `browser` | 浏览器自动化 | 免费 |

**问题**: 默认`web_search`需要Brave API Key，且Brave已取消免费套餐。

---

## 其他AI Agent项目实现

### 1. LangChain搜索工具

LangChain提供了丰富的搜索集成：

```python
# DuckDuckGo（免费）
from langchain_community.tools import DuckDuckGoSearchRun
ddg_search = DuckDuckGoSearchRun()

# Tavily（免费额度）
from langchain_community.tools import TavilySearchResults
tavily = TavilySearchResults()

# Google Serper（需要API Key）
from langchain_community.utilities import GoogleSerperAPIWrapper
serper = GoogleSerperAPIWrapper()
```

### 2. AutoGPT搜索实现

AutoGPT使用`SearchTool`进行网络搜索：

```python
from autogpt.tools import SearchTool

search_tool = SearchTool(
    name="web_search",
    description="Search the web for information",
    params={
        "search_engine": "duckduckgo",  # 可使用DuckDuckGo
        "max_results": 5,
        "language": "en"
    }
)
```

### 3. MCP Servers搜索实现

MCP生态有多种免费搜索服务器：

| MCP Server | 技术 | 费用 | 特点 |
|-----------|------|------|------|
| One Search | Puppeteer本地浏览器 | 免费 | 支持多引擎 |
| Open Web Search | 直接抓取 | 免费 | Docker部署 |
| SearXNG MCP | SearXNG | 免费 | 自托管 |
| DuckDuckGo MCP | DDGS | 免费 | 轻量级 |

### 4. 社区DDG Search Skill

韩国社区开发的DuckDuckGo搜索技能：

```yaml
# ~/.openclaw/workspace/skills/ddg-search/SKILL.md
name: ddg-search
description: DuckDuckGo-based web search without requiring API keys
```

---

## 推荐方案

### 🏆 第一推荐：DuckDuckGo Search (ddgs)

**适用场景**: 个人使用、开发测试、轻量级应用

**实现代码**:
```python
from duckduckgo_search import DDGS

def free_search(query: str, max_results: int = 5):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    return [
        {"title": r["title"], "url": r["href"], "snippet": r["body"]}
        for r in results
    ]
```

**部署难度**: ⭐⭐  
**成本**: $0  
**可靠性**: ⭐⭐⭐⭐

---

### 🏆 第二推荐：SearXNG自建搜索

**适用场景**: 团队使用、生产环境、高隐私要求

**部署方案**:
```bash
# Docker Compose部署
version: '3'
services:
  searxng:
    image: searxng/searxng:latest
    ports:
      - "8888:8080"
    volumes:
      - ./config:/etc/searxng
    environment:
      - BASE_URL=http://localhost:8888/
```

**部署难度**: ⭐⭐⭐⭐  
**成本**: $5-10/月（VPS）  
**可靠性**: ⭐⭐⭐⭐⭐

---

### 🏆 第三推荐：混合方案

**策略**: DuckDuckGo为主 + 浏览器抓取为辅

```python
from duckduckgo_search import DDGS
from playwright.sync_api import sync_playwright

def hybrid_search(query: str):
    # 第一步：DuckDuckGo搜索
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
    
    # 第二步：抓取详细内容
    detailed_results = []
    for result in results:
        try:
            content = fetch_with_playwright(result['href'])
            detailed_results.append({
                "title": result['title'],
                "url": result['href'],
                "content": content[:2000]  # 限制长度
            })
        except:
            detailed_results.append(result)
    
    return detailed_results

def fetch_with_playwright(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=30000)
        content = page.evaluate("document.body.innerText")
        browser.close()
        return content
```

**部署难度**: ⭐⭐⭐  
**成本**: $0  
**可靠性**: ⭐⭐⭐⭐

---

### 🏆 第四推荐：OpenClaw Skill集成方案

建议为OpenClaw创建一个内置的免费搜索skill：

```yaml
# skills/free-search/SKILL.md
name: free-search
description: |
  Free web search using DuckDuckGo. No API key required.
  Use this as the default search skill when web_search is unavailable.
---

## Usage

```bash
python3 ~/.openclaw/skills/free-search/scripts/search.py "query" --max-results 5
```
```

**实现脚本**:
```python
#!/usr/bin/env python3
# skills/free-search/scripts/search.py
import json
import sys
import argparse
from duckduckgo_search import DDGS

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max-results", type=int, default=5)
    args = parser.parse_args()
    
    with DDGS() as ddgs:
        results = list(ddgs.text(args.query, max_results=args.max_results))
    
    output = {
        "query": args.query,
        "results": [{"title": r["title"], "url": r["href"], "snippet": r["body"]} for r in results],
        "count": len(results)
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

---

## 结论与建议

### 方案对比总结

| 方案 | 费用 | 难度 | 可靠性 | 适用场景 |
|------|------|------|--------|----------|
| DuckDuckGo (ddgs) | 免费 | ⭐⭐ | ⭐⭐⭐⭐ | 个人/开发 |
| SearXNG自建 | 免费+服务器 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 团队/生产 |
| Brave API | ~1k/月免费 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 商业应用 |
| Google Custom | 100/天免费 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 轻量应用 |
| Tavily | 1k/月免费 | ⭐⭐ | ⭐⭐⭐⭐ | AI应用 |
| 网页抓取 | 免费 | ⭐⭐⭐ | ⭐⭐⭐ | 补充方案 |

### 实施建议

1. **立即行动**：安装`duckduckgo-search`库作为默认免费搜索方案
2. **中期规划**：部署SearXNG实例用于团队/生产环境
3. **备选方案**：申请Brave API Key作为高可靠性备选
4. **架构设计**：实现三级回退策略（Brave → DuckDuckGo → 浏览器）

### 参考链接

- [DuckDuckGo Search Python](https://github.com/deedy5/duckduckgo-search)
- [SearXNG Documentation](https://docs.searxng.org/)
- [LangChain Search Tools](https://python.langchain.com/docs/integrations/tools/)
- [One Search MCP Server](https://github.com/yokingma/one-search-mcp)

---

*报告生成时间: 2026年3月12日*  
*作者: OpenClaw AI Agent*

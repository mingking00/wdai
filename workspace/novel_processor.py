#!/usr/bin/env python3
"""
Vibero Novel Processor - 小说双语处理器
输入: 中文小说TXT
输出: 交互式双语HTML阅读器
"""

import re
import json
import os
import sys
from pathlib import Path

# 需要安装的依赖
try:
    import requests
except ImportError:
    print("请先安装依赖: pip install requests")
    sys.exit(1)

class NovelProcessor:
    def __init__(self, api_key, base_url="https://api.moonshot.cn/v1", model="moonshot-v1-8k"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.novel_data = {
            "title": "",
            "chapters": [],
            "characters": [],
            "concepts": []
        }
    
    def call_ai(self, prompt, system="你是一个专业的小说分析助手"):
        """调用AI API"""
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"API调用失败: {e}")
            return None
    
    def parse_novel(self, text):
        """解析小说结构"""
        print("📖 分析小说结构...")
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # 检测标题（第一行或特殊格式）
        title = lines[0] if lines else "Unknown Novel"
        if len(title) > 50 or '作者' in title or '作者：' in title:
            title = "Unknown Novel"
        
        # 检测章节
        chapter_pattern = r'^(第[一二三四五六七八九十百千万\d]+章|Chapter\s*\d+|\d+\s*\.|【|\[)'
        chapters = []
        current_chapter = {"title": "序章", "content": []}
        
        for line in lines[1:] if title != "Unknown Novel" else lines:
            if re.match(chapter_pattern, line, re.IGNORECASE) and len(line) < 100:
                if current_chapter["content"]:
                    chapters.append(current_chapter)
                current_chapter = {"title": line, "content": []}
            elif len(line) > 20:
                current_chapter["content"].append(line)
        
        if current_chapter["content"]:
            chapters.append(current_chapter)
        
        # 如果没有检测到章节，按段落分
        if len(chapters) == 0:
            paragraphs = [l for l in lines if len(l) > 20]
            chunk_size = max(1, len(paragraphs) // 10)
            for i in range(0, len(paragraphs), chunk_size):
                chunk = paragraphs[i:i+chunk_size]
                chapters.append({
                    "title": f"第{i//chunk_size + 1}部分",
                    "content": chunk
                })
        
        self.novel_data["title"] = title
        self.novel_data["chapters"] = chapters
        
        print(f"✅ 发现 {len(chapters)} 个章节，共 {sum(len(c['content']) for c in chapters)} 段")
        return chapters
    
    def extract_terms(self):
        """提取人物和概念"""
        print("🔍 提取人物和概念...")
        
        # 收集样本（每章前2段，最多20段）
        samples = []
        for ch in self.novel_data["chapters"][:10]:
            for para in ch["content"][:2]:
                if len(para) > 30:
                    samples.append(para)
        
        sample_text = '\n\n'.join(samples[:20])
        
        prompt = f"""分析以下中文小说内容，提取关键术语。

要求：
1. **人物**：主角、重要配角（姓名+身份+性格特点）
2. **地点**：重要场景、城市、建筑
3. **组织**：门派、公司、势力
4. **概念**：核心设定、关键物品、特殊能力

对每个术语提供：
- name: 中文名
- enName: 英文名（音译或意译）
- category: 分类（人物/地点/组织/概念/物品）
- description: 一句话描述
- importance: 重要性（核心/重要/次要）

返回严格JSON格式：
[{{
  "name": "示例人物",
  "enName": "Example Character", 
  "category": "人物",
  "description": "主角，性格坚毅",
  "importance": "核心"
}}]

小说样本：
{sample_text[:3000]}"""

        result = self.call_ai(prompt)
        if not result:
            return
        
        # 解析JSON
        try:
            json_match = re.search(r'\[[\s\S]*\]', result)
            if json_match:
                terms = json.loads(json_match.group())
                
                for term in terms:
                    item = {
                        "id": f"{term['category']}_{term['name']}",
                        "name": term['name'],
                        "enName": term.get('enName', term['name']),
                        "description": term.get('description', ''),
                        "importance": term.get('importance', '重要')
                    }
                    
                    if term['category'] == '人物':
                        item['role'] = term.get('description', 'Character').split('，')[0]
                        item['color'] = self._get_color(len(self.novel_data['characters']))
                        item['quote'] = ''
                        self.novel_data['characters'].append(item)
                    else:
                        item['category'] = term['category']
                        self.novel_data['concepts'].append(item)
                
                print(f"✅ 提取了 {len(self.novel_data['characters'])} 个人物，{len(self.novel_data['concepts'])} 个概念")
        except Exception as e:
            print(f"术语解析失败: {e}")
    
    def _get_color(self, index):
        """获取颜色"""
        colors = ['#E74C3C', '#3498DB', '#27AE60', '#9B59B6', '#F39C12', '#1ABC9C', '#E67E22', '#8E44AD']
        return colors[index % len(colors)]
    
    def translate_chapters(self, progress_callback=None):
        """翻译章节"""
        print("🌐 开始翻译...")
        
        total = sum(len(c['content']) for c in self.novel_data['chapters'])
        translated = 0
        
        for ch_idx, chapter in enumerate(self.novel_data['chapters']):
            print(f"  翻译第 {ch_idx+1}/{len(self.novel_data['chapters'])} 章...")
            
            chapter['paragraphs'] = []
            
            for para_idx, para in enumerate(chapter['content']):
                # 短句不翻译
                if len(para) < 10:
                    chapter['paragraphs'].append({
                        'zh': para,
                        'en': para
                    })
                    continue
                
                prompt = f"""将以下中文翻译成流畅的英文：

要求：
1. 保持文学性和流畅度
2. 人名地名用拼音（如：张三 → Zhang San）
3. 只返回翻译结果，不要解释

中文：
{para}

英文："""
                
                result = self.call_ai(prompt, "你是一个专业的小说翻译助手")
                
                if result:
                    chapter['paragraphs'].append({
                        'zh': para,
                        'en': result.strip()
                    })
                else:
                    chapter['paragraphs'].append({
                        'zh': para,
                        'en': '[Translation pending]'
                    })
                
                translated += 1
                if progress_callback:
                    progress_callback(translated, total)
                
                # 避免API限流
                import time
                time.sleep(0.3)
        
        print("✅ 翻译完成")
    
    def generate_html(self, output_path):
        """生成HTML"""
        print("🎨 生成交互式HTML...")
        
        html_content = self._build_html()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ 已保存到: {output_path}")
        return output_path
    
    def _build_html(self):
        """构建HTML内容"""
        data_json = json.dumps(self.novel_data, ensure_ascii=False)
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.novel_data['title']} - Vibero Reader</title>
    <style>
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a28;
            --accent: #ff6b6b;
            --accent-gradient: linear-gradient(135deg, #ff6b6b 0%, #ff8e53 100%);
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --text-muted: #606070;
            --border: rgba(255,255,255,0.08);
            --card-bg: rgba(255,255,255,0.03);
            --hover-bg: rgba(255,255,255,0.06);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            overflow: hidden;
            line-height: 1.6;
        }}
        .app {{ display: grid; grid-template-rows: 60px 1fr; height: 100vh; }}
        .header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
        }}
        .logo {{
            font-size: 20px;
            font-weight: 700;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .main {{ display: grid; grid-template-columns: 300px 1fr 340px; overflow: hidden; }}
        
        /* Sidebar Left */
        .sidebar-left {{
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            overflow-y: auto;
            padding: 20px;
        }}
        .sidebar-section {{ margin-bottom: 24px; }}
        .section-title {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .section-count {{
            background: var(--card-bg);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
        }}
        
        /* Chapter List */
        .chapter-item {{
            padding: 12px 16px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 4px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .chapter-item:hover {{ background: var(--hover-bg); }}
        .chapter-item.active {{
            background: var(--card-bg);
            border: 1px solid var(--border);
        }}
        .chapter-item.active .chapter-num {{
            background: var(--accent);
            color: white;
        }}
        .chapter-num {{
            width: 28px;
            height: 28px;
            border-radius: 8px;
            background: var(--bg-tertiary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
        }}
        
        /* Character Cards */
        .char-grid {{ display: grid; gap: 8px; }}
        .char-card {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-radius: 12px;
            background: var(--card-bg);
            cursor: pointer;
            transition: all 0.2s;
        }}
        .char-card:hover {{ background: var(--hover-bg); transform: translateX(4px); }}
        .char-avatar {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: 700;
            color: white;
        }}
        .char-info {{ flex: 1; }}
        .char-name {{ font-weight: 600; font-size: 14px; }}
        .char-en {{ font-size: 12px; color: var(--text-muted); }}
        .char-role {{ font-size: 11px; color: var(--accent); margin-top: 2px; }}
        
        /* Concept List */
        .concept-list {{ display: flex; flex-direction: column; gap: 8px; }}
        .concept-item {{
            padding: 12px;
            border-radius: 10px;
            background: var(--card-bg);
            cursor: pointer;
            transition: all 0.2s;
        }}
        .concept-item:hover {{ border: 1px solid var(--accent); }}
        .concept-name {{ font-weight: 600; font-size: 14px; }}
        .concept-en {{ font-size: 12px; color: var(--accent); }}
        .concept-desc {{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }}
        
        /* Reader */
        .reader {{ display: flex; flex-direction: column; overflow: hidden; }}
        .reader-toolbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 32px;
            border-bottom: 1px solid var(--border);
            background: var(--bg-secondary);
        }}
        .view-options {{
            display: flex;
            gap: 4px;
            background: var(--bg-primary);
            padding: 4px;
            border-radius: 10px;
        }}
        .view-btn {{
            padding: 8px 16px;
            border-radius: 8px;
            border: none;
            background: transparent;
            color: var(--text-muted);
            font-size: 13px;
            cursor: pointer;
        }}
        .view-btn.active {{ background: var(--card-bg); color: var(--text-primary); }}
        
        .reader-content {{
            flex: 1;
            overflow-y: auto;
            padding: 40px 48px;
        }}
        
        /* Content */
        .chapter-header {{
            margin-bottom: 40px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
        }}
        .chapter-heading {{
            font-size: 32px;
            font-weight: 700;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .chapter-subheading {{
            font-size: 18px;
            color: var(--text-secondary);
            margin-top: 8px;
        }}
        
        .para-block {{
            margin-bottom: 32px;
            padding: 20px 24px;
            border-radius: 16px;
            background: var(--card-bg);
        }}
        .para-block:hover {{ border: 1px solid var(--border); }}
        
        .zh-text {{
            font-size: 17px;
            line-height: 1.9;
            margin-bottom: 12px;
        }}
        .en-text {{
            font-size: 15px;
            line-height: 1.7;
            color: var(--text-secondary);
            padding-left: 16px;
            border-left: 3px solid var(--accent);
        }}
        
        /* Term Highlight */
        .term {{
            background: rgba(255,107,107,0.15);
            padding: 2px 8px;
            border-radius: 6px;
            cursor: pointer;
            border-bottom: 2px solid var(--accent);
            position: relative;
        }}
        .term:hover {{ background: rgba(255,107,107,0.3); }}
        
        /* Tooltip */
        .term-wrapper {{ position: relative; display: inline; }}
        .term-tooltip {{
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%) translateY(-8px);
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            min-width: 220px;
            max-width: 300px;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s;
        }}
        .term-wrapper:hover .term-tooltip {{
            opacity: 1;
            visibility: visible;
        }}
        .tooltip-zh {{ font-size: 16px; font-weight: 600; }}
        .tooltip-en {{ font-size: 13px; color: var(--accent); }}
        .tooltip-desc {{ font-size: 12px; color: var(--text-secondary); margin-top: 8px; }}
        
        /* Sidebar Right */
        .sidebar-right {{
            background: var(--bg-secondary);
            border-left: 1px solid var(--border);
            overflow-y: auto;
            padding: 20px;
        }}
        .detail-card {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
        }}
        .detail-header {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 20px;
        }}
        .detail-avatar {{
            width: 64px;
            height: 64px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: 700;
            color: white;
        }}
        .detail-name {{ font-size: 24px; font-weight: 700; }}
        .detail-en {{ font-size: 16px; color: var(--accent); }}
        .detail-section {{ margin-bottom: 20px; }}
        .detail-section-title {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}
        .detail-text {{ font-size: 14px; color: var(--text-secondary); line-height: 1.7; }}
        .quote-box {{
            background: var(--bg-tertiary);
            border-left: 4px solid var(--accent);
            padding: 16px 20px;
            border-radius: 0 12px 12px 0;
            font-style: italic;
            color: var(--text-secondary);
        }}
    </style>
</head>
<body>
    <div id="app"></div>
    
    <script>
        // 嵌入的小说数据
        const novelData = {data_json};
        let currentChapter = 0;
        
        function escapeRegExp(string) {{
            return string.replace(/[.*+?^${{}}()|[\]\\]/g, '\\$&');
        }}
        
        function getRandomColor(index) {{
            const colors = ['#E74C3C', '#3498DB', '#27AE60', '#9B59B6', '#F39C12', '#1ABC9C'];
            return colors[index % colors.length];
        }}
        
        function renderApp() {{
            const app = document.getElementById('app');
            app.innerHTML = `
                <div class="app">
                    <header class="header">
                        <div class="logo">📖 ${{novelData.title}}</div>
                        <div class="view-options">
                            <button class="view-btn active" onclick="setView('bilingual')">双语</button>
                            <button class="view-btn" onclick="setView('zh')">中文</button>
                            <button class="view-btn" onclick="setView('en')">English</button>
                        </div>
                    </header>
                    <div class="main">
                        <aside class="sidebar-left">
                            <div class="sidebar-section">
                                <div class="section-title">
                                    章节
                                    <span class="section-count">${{novelData.chapters.length}}</span>
                                </div>
                                <div id="chapter-list"></div>
                            </div>
                            ${{novelData.characters.length > 0 ? `
                            <div class="sidebar-section">
                                <div class="section-title">
                                    人物
                                    <span class="section-count">${{novelData.characters.length}}</span>
                                </div>
                                <div class="char-grid" id="char-list"></div>
                            </div>
                            ` : ''}}
                            ${{novelData.concepts.length > 0 ? `
                            <div class="sidebar-section">
                                <div class="section-title">
                                    概念
                                    <span class="section-count">${{novelData.concepts.length}}</span>
                                </div>
                                <div class="concept-list" id="concept-list"></div>
                            </div>
                            ` : ''}}
                        </aside>
                        <main class="reader">
                            <div class="reader-toolbar">
                                <span style="color: var(--text-muted);">Chapter ${{currentChapter + 1}} / ${{novelData.chapters.length}}</span>
                            </div>
                            <div class="reader-content" id="reader-content"></div>
                        </main>
                        <aside class="sidebar-right" id="sidebar-right">
                            <div class="detail-card">
                                <div class="detail-section-title">Welcome</div>
                                <div class="detail-text">Click on highlighted terms to view details.</div>
                            </div>
                        </aside>
                    </div>
                </div>
            `;
            
            renderChapterList();
            renderCharList();
            renderConceptList();
            renderChapter(0);
        }}
        
        function renderChapterList() {{
            const container = document.getElementById('chapter-list');
            if (!container) return;
            container.innerHTML = novelData.chapters.map((ch, i) => `
                <div class="chapter-item ${{i === currentChapter ? 'active' : ''}}" onclick="goToChapter(${{i}})">
                    <div class="chapter-num">${{i + 1}}</div>
                    <div style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${{ch.title}}</div>
                </div>
            `).join('');
        }}
        
        function renderCharList() {{
            const container = document.getElementById('char-list');
            if (!container) return;
            container.innerHTML = novelData.characters.map(char => `
                <div class="char-card" onclick="showCharDetail('${{char.id}}')">
                    <div class="char-avatar" style="background: ${{char.color}}">${{char.name[0]}}</div>
                    <div class="char-info">
                        <div class="char-name">${{char.name}}</div>
                        <div class="char-en">${{char.enName}}</div>
                        <div class="char-role">${{char.role}}</div>
                    </div>
                </div>
            `).join('');
        }}
        
        function renderConceptList() {{
            const container = document.getElementById('concept-list');
            if (!container) return;
            container.innerHTML = novelData.concepts.map(concept => `
                <div class="concept-item" onclick="showConceptDetail('${{concept.id}}')">
                    <div class="concept-name">${{concept.name}}</div>
                    <div class="concept-en">${{concept.enName}}</div>
                    <div class="concept-desc">${{concept.description?.substring(0, 50) || ''}}...</div>
                </div>
            `).join('');
        }}
        
        function highlightTerms(text) {{
            const allTerms = [...novelData.characters, ...novelData.concepts]
                .sort((a, b) => b.name.length - a.name.length);
            
            allTerms.forEach(item => {{
                const escaped = escapeRegExp(item.name);
                const regex = new RegExp(escaped, 'g');
                text = text.replace(regex, match => `
                    <span class="term-wrapper">
                        <span class="term" onclick="handleTermClick('${{item.id}}')">${{match}}</span>
                        <div class="term-tooltip">
                            <div class="tooltip-zh">${{item.name}}</div>
                            <div class="tooltip-en">${{item.enName}}</div>
                            <div class="tooltip-desc">${{item.description?.substring(0, 60) || ''}}...</div>
                        </div>
                    </span>
                `);
            }});
            return text;
        }}
        
        function handleTermClick(id) {{
            const char = novelData.characters.find(c => c.id === id);
            if (char) return showCharDetail(id);
            const concept = novelData.concepts.find(c => c.id === id);
            if (concept) return showConceptDetail(id);
        }}
        
        function renderChapter(index) {{
            currentChapter = index;
            const chapter = novelData.chapters[index];
            const container = document.getElementById('reader-content');
            if (!container) return;
            
            let html = `
                <div class="chapter-header">
                    <h1 class="chapter-heading">${{chapter.title}}</h1>
                </div>
            `;
            
            chapter.paragraphs.forEach(para => {{
                html += `<div class="para-block">`;
                html += `<div class="zh-text">${{highlightTerms(para.zh)}}</div>`;
                if (para.en && para.en !== para.zh) {{
                    html += `<div class="en-text">${{para.en}}</div>`;
                }}
                html += `</div>`;
            }});
            
            container.innerHTML = html;
            container.scrollTop = 0;
            
            document.querySelectorAll('.chapter-item').forEach((el, i) => {{
                el.classList.toggle('active', i === index);
            }});
        }}
        
        function goToChapter(index) {{
            renderChapter(index);
        }}
        
        function showCharDetail(charId) {{
            const char = novelData.characters.find(c => c.id === charId);
            if (!char) return;
            
            document.getElementById('sidebar-right').innerHTML = `
                <div class="detail-card">
                    <div class="detail-header">
                        <div class="detail-avatar" style="background: ${{char.color}}">${{char.name[0]}}</div>
                        <div>
                            <div class="detail-name">${{char.name}}</div>
                            <div class="detail-en">${{char.enName}}</div>
                        </div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-section-title">Role</div>
                        <div class="detail-text">${{char.role}}</div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-section-title">Description</div>
                        <div class="detail-text">${{char.description}}</div>
                    </div>
                    ${{char.quote ? `
                    <div class="detail-section">
                        <div class="detail-section-title">Quote</div>
                        <div class="quote-box">"${{char.quote}}"</div>
                    </div>
                    ` : ''}}
                </div>
            `;
        }}
        
        function showConceptDetail(conceptId) {{
            const concept = novelData.concepts.find(c => c.id === conceptId);
            if (!concept) return;
            
            document.getElementById('sidebar-right').innerHTML = `
                <div class="detail-card">
                    <div class="detail-header">
                        <div class="detail-avatar" style="background: #666">📖</div>
                        <div>
                            <div class="detail-name">${{concept.name}}</div>
                            <div class="detail-en">${{concept.enName}}</div>
                        </div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-section-title">Category</div>
                        <span style="background: var(--card-bg); padding: 4px 12px; border-radius: 8px; font-size: 13px;">${{concept.category}}</span>
                    </div>
                    <div class="detail-section">
                        <div class="detail-section-title">Description</div>
                        <div class="detail-text">${{concept.description}}</div>
                    </div>
                    ${{concept.importance ? `
                    <div class="detail-section">
                        <div class="detail-section-title">Importance</div>
                        <div class="quote-box">${{concept.importance}}</div>
                    </div>
                    ` : ''}}
                </div>
            `;
        }}
        
        function setView(mode) {{
            document.querySelectorAll('.view-btn').forEach(btn => {{
                btn.classList.remove('active');
                if (btn.textContent.includes(mode === 'bilingual' ? '双语' : mode === 'zh' ? '中文' : 'English')) {{
                    btn.classList.add('active');
                }}
            }});
            
            document.querySelectorAll('.para-block').forEach(block => {{
                const zh = block.querySelector('.zh-text');
                const en = block.querySelector('.en-text');
                if (zh) zh.style.display = mode === 'en' ? 'none' : 'block';
                if (en) en.style.display = mode === 'zh' ? 'none' : 'block';
            }});
        }}
        
        // 启动
        renderApp();
    </script>
</body>
</html>'''


def main():
    print("=" * 60)
    print("  Vibero Novel Processor - 小说双语处理器")
    print("=" * 60)
    print()
    
    # 获取API Key
    api_key = input("请输入 Kimi API Key (从 https://platform.moonshot.cn 获取): ").strip()
    if not api_key:
        print("❌ 需要API Key才能继续")
        return
    
    # 获取文件路径
    txt_path = input("请输入小说TXT文件路径: ").strip()
    if not os.path.exists(txt_path):
        print(f"❌ 文件不存在: {txt_path}")
        return
    
    # 读取文件
    print(f"📖 读取文件: {txt_path}")
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"   文件大小: {len(text)} 字符")
    print()
    
    # 创建处理器
    processor = NovelProcessor(api_key)
    
    # 解析小说
    processor.parse_novel(text)
    print()
    
    # 提取术语
    processor.extract_terms()
    print()
    
    # 询问是否翻译
    translate = input("是否翻译全文? (y/n): ").strip().lower() == 'y'
    
    if translate:
        print()
        processor.translate_chapters()
    else:
        # 不翻译时保留原文
        for ch in processor.novel_data['chapters']:
            ch['paragraphs'] = [
                {'zh': para, 'en': '[Not translated]'}
                for para in ch['content']
            ]
    
    # 生成输出路径
    output_name = Path(txt_path).stem + "_ bilingual.html"
    output_path = os.path.join(os.path.dirname(txt_path) or '.', output_name)
    
    print()
    processor.generate_html(output_path)
    
    print()
    print("=" * 60)
    print(f"✅ 完成! 输出文件: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

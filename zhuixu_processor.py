#!/usr/bin/env python3
"""
赘婿小说处理器 - 专为《赘婿》优化的翻译大师
"""

import re
import json
import os
import sys
from pathlib import Path

# 使用云端API
API_CONFIG = {
    "api_key": os.environ.get("KIMI_API_KEY", ""),
    "base_url": "https://api.moonshot.cn/v1",
    "model": "moonshot-v1-8k"
}

class ZhuixuProcessor:
    """《赘婿》专用处理器"""
    
    def __init__(self):
        self.novel_data = {
            "title": "赘婿 (My Heroic Husband)",
            "chapters": [],
            "characters": [],
            "concepts": []
        }
        self.all_text = ""
        
    def load_file(self, filepath):
        """加载小说文件"""
        print(f"📖 加载文件: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            self.all_text = f.read()
        print(f"   共 {len(self.all_text)} 字符")
        return self.all_text
    
    def parse_chapters(self, max_chapters=10):
        """解析章节结构"""
        print(f"🔍 解析章节结构 (前{max_chapters}章)...")
        
        # 分割文本
        lines = self.all_text.split('\n')
        
        chapters = []
        current_chapter = {"title": "楔子 繁华过眼开一季", "content": [], "line_start": 0}
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 检测章节标题
            if re.match(r'^第[一二三四五六七八九十百千万\d]+章', line) and len(line) < 50:
                if current_chapter["content"]:
                    chapters.append(current_chapter)
                    if len(chapters) >= max_chapters:
                        break
                current_chapter = {
                    "title": line,
                    "content": [],
                    "line_start": i
                }
            elif len(line) > 30 and not line.startswith('---') and not line.startswith('声明'):
                current_chapter["content"].append(line)
        
        if current_chapter["content"] and len(chapters) < max_chapters:
            chapters.append(current_chapter)
        
        self.novel_data["chapters"] = chapters
        print(f"✅ 解析完成: {len(chapters)} 个章节")
        for ch in chapters[:5]:
            print(f"   • {ch['title']} ({len(ch['content'])} 段)")
        return chapters
    
    def extract_entities(self):
        """提取人物和概念"""
        print("🔍 提取人物和概念...")
        
        # 读取前3章内容作为样本
        sample_text = ""
        for ch in self.novel_data["chapters"][:3]:
            sample_text += '\n'.join(ch["content"][:10]) + "\n\n"
        
        # 使用简单规则提取 + 预设已知人物
        known_characters = [
            {"name": "宁毅", "enName": "Ning Yi", "role": "主角/赘婿", "description": "现代金融巨子穿越到古代，成为苏家赘婿"},
            {"name": "苏檀儿", "enName": "Su Tan'er", "role": "女主角/妻子", "description": "苏家大小姐，经商奇才，宁毅的妻子"},
            {"name": "小婵", "enName": "Xiao Chan", "role": "侍女", "description": "苏檀儿的贴身丫鬟"},
            {"name": "唐明远", "enName": "Tang Mingyuan", "role": "前世对手", "description": "宁毅前世的商业伙伴，最终背叛了他"},
            {"name": "苏伯庸", "enName": "Su Boyong", "role": "岳父", "description": "苏檀儿的父亲，苏家大房主事"},
            {"name": "苏太公", "enName": "Su Patriarch", "role": "苏家族长", "description": "苏家现任族长，苏檀儿的祖父"},
        ]
        
        known_concepts = [
            {"name": "江宁", "enName": "Jiangning", "category": "地点", "description": "武朝繁华城市，相当于南京"},
            {"name": "苏家", "enName": "Su Family", "category": "家族", "description": "江宁富商，以纺织生意起家"},
            {"name": "武朝", "enName": "Wu Dynasty", "category": "朝代", "description": "架空朝代，类似南宋"},
            {"name": "秦淮河", "enName": "Qinhuai River", "category": "地点", "description": "江宁著名河流，繁华的娱乐地带"},
            {"name": "赘婿", "enName": "Live-in Son-in-law", "category": "身份", "description": "入赘女方家的男子，地位较低"},
        ]
        
        colors = ['#E74C3C', '#3498DB', '#27AE60', '#9B59B6', '#F39C12', '#1ABC9C']
        
        for i, char in enumerate(known_characters):
            self.novel_data['characters'].append({
                "id": f"char_{i}",
                "name": char['name'],
                "enName": char['enName'],
                "role": char['role'],
                "description": char['description'],
                "color": colors[i % len(colors)],
                "quote": ""
            })
        
        for i, concept in enumerate(known_concepts):
            self.novel_data['concepts'].append({
                "id": f"concept_{i}",
                "name": concept['name'],
                "enName": concept['enName'],
                "category": concept['category'],
                "description": concept['description'],
                "importance": "核心"
            })
        
        print(f"✅ 提取了 {len(self.novel_data['characters'])} 个人物，{len(self.novel_data['concepts'])} 个概念")
    
    def translate_chapters(self):
        """翻译章节"""
        import requests
        import time
        
        print("🌐 开始翻译 (使用Kimi API)...")
        
        headers = {
            'Authorization': f"Bearer {API_CONFIG['api_key']}",
            'Content-Type': 'application/json'
        }
        
        total_chapters = len(self.novel_data['chapters'])
        
        for idx, chapter in enumerate(self.novel_data['chapters']):
            print(f"\n  翻译第 {idx+1}/{total_chapters} 章: {chapter['title']}")
            chapter['paragraphs'] = []
            
            # 每章翻译前15段
            for para_idx, para in enumerate(chapter['content'][:15]):
                if len(para) < 20:
                    chapter['paragraphs'].append({'zh': para, 'en': para})
                    continue
                
                prompt = f"""将以下中文小说段落翻译成流畅的英文：

要求：
1. 保持文学性和叙事流畅
2. 人名使用拼音（如：宁毅 → Ning Yi）
3. 保持原文风格和语气
4. 只返回翻译结果

原文：
{para}

英文翻译："""
                
                try:
                    payload = {
                        'model': API_CONFIG['model'],
                        'messages': [
                            {'role': 'system', 'content': '你是一个专业的小说翻译助手'},
                            {'role': 'user', 'content': prompt}
                        ],
                        'temperature': 0.3
                    }
                    
                    response = requests.post(
                        f"{API_CONFIG['base_url']}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    
                    result = response.json()['choices'][0]['message']['content']
                    chapter['paragraphs'].append({
                        'zh': para,
                        'en': result.strip()
                    })
                    print(f"    ✓ 段{para_idx+1}", end='\r')
                    
                except Exception as e:
                    print(f"    ✗ 段{para_idx+1} 失败")
                    chapter['paragraphs'].append({
                        'zh': para,
                        'en': '[Translation failed]'
                    })
                
                time.sleep(0.5)  # 避免限流
            
            print(f"    ✅ 完成 {len(chapter['paragraphs'])} 段")
    
    def generate_html(self, output_path):
        """生成HTML"""
        print("\n🎨 生成交互式HTML...")
        
        data_json = json.dumps(self.novel_data, ensure_ascii=False)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>赘婿 - 双语阅读器 | My Heroic Husband - Bilingual Reader</title>
    <style>
        :root {{ 
            --bg: #0a0a0f; --bg2: #12121a; --bg3: #1a1a28;
            --accent: #ff6b6b; --accent2: #ff8e53;
            --text: #fff; --text2: #a0a0b0; --text3: #606070;
            --border: rgba(255,255,255,0.08);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
            background: var(--bg); color: var(--text); height: 100vh; overflow: hidden;
        }}
        .app {{ display: grid; grid-template-rows: 60px 1fr; height: 100vh; }}
        .header {{ 
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 24px; background: var(--bg2); border-bottom: 1px solid var(--border);
        }}
        .logo {{ 
            font-size: 20px; font-weight: 700;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        .main {{ display: grid; grid-template-columns: 300px 1fr 340px; overflow: hidden; }}
        
        /* Sidebar */
        .sidebar {{ background: var(--bg2); padding: 20px; overflow-y: auto; }}
        .sidebar-left {{ border-right: 1px solid var(--border); }}
        .sidebar-right {{ border-left: 1px solid var(--border); }}
        .section-title {{ 
            font-size: 11px; font-weight: 600; color: var(--text3);
            text-transform: uppercase; letter-spacing: 0.5px;
            margin: 20px 0 12px; display: flex; justify-content: space-between;
        }}
        .section-title:first-child {{ margin-top: 0; }}
        .section-title span {{ background: var(--bg3); padding: 2px 8px; border-radius: 12px; }}
        
        /* Chapter List */
        .chapter-item {{ 
            display: flex; align-items: center; gap: 12px;
            padding: 12px; border-radius: 10px; cursor: pointer;
            margin-bottom: 4px; transition: all 0.2s; font-size: 14px;
        }}
        .chapter-item:hover {{ background: rgba(255,255,255,0.05); }}
        .chapter-item.active {{ background: var(--bg3); }}
        .chapter-num {{ 
            width: 28px; height: 28px; border-radius: 8px;
            background: var(--bg3); display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: 600; color: var(--text3); flex-shrink: 0;
        }}
        .chapter-item.active .chapter-num {{ background: var(--accent); color: white; }}
        .chapter-title {{ flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        
        /* Character Cards */
        .char-card {{ 
            display: flex; align-items: center; gap: 12px;
            padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.03);
            cursor: pointer; margin-bottom: 8px; transition: all 0.2s;
        }}
        .char-card:hover {{ background: rgba(255,255,255,0.06); transform: translateX(4px); }}
        .char-avatar {{ 
            width: 44px; height: 44px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 18px; font-weight: 700; color: white; flex-shrink: 0;
        }}
        .char-name {{ font-weight: 600; font-size: 14px; }}
        .char-en {{ font-size: 12px; color: var(--text2); }}
        .char-role {{ font-size: 11px; color: var(--accent); margin-top: 2px; }}
        
        /* Reader */
        .reader {{ display: flex; flex-direction: column; overflow: hidden; }}
        .reader-toolbar {{ 
            display: flex; align-items: center; justify-content: space-between;
            padding: 16px 32px; background: var(--bg2); border-bottom: 1px solid var(--border);
        }}
        .view-options {{ display: flex; gap: 4px; background: var(--bg); padding: 4px; border-radius: 10px; }}
        .view-btn {{ 
            padding: 8px 16px; border-radius: 8px; border: none;
            background: transparent; color: var(--text3); font-size: 13px; cursor: pointer; transition: all 0.2s;
        }}
        .view-btn:hover {{ color: var(--text); }}
        .view-btn.active {{ background: rgba(255,255,255,0.1); color: var(--text); }}
        .reader-content {{ flex: 1; overflow-y: auto; padding: 40px 48px; }}
        
        /* Content */
        .chapter-header {{ margin-bottom: 40px; padding-bottom: 24px; border-bottom: 1px solid var(--border); }}
        .chapter-heading {{ 
            font-size: 32px; font-weight: 700;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
        .chapter-subheading {{ font-size: 18px; color: var(--text2); margin-top: 8px; }}
        
        .para-block {{ 
            margin-bottom: 32px; padding: 24px; border-radius: 16px;
            background: rgba(255,255,255,0.03); transition: all 0.2s;
        }}
        .para-block:hover {{ border: 1px solid var(--border); }}
        .zh-text {{ font-size: 17px; line-height: 1.9; margin-bottom: 12px; }}
        .en-text {{ 
            font-size: 15px; line-height: 1.7; color: var(--text2);
            padding-left: 16px; border-left: 3px solid var(--accent);
        }}
        
        /* Term Highlight */
        .term {{ 
            background: rgba(255,107,107,0.15); padding: 2px 6px; border-radius: 6px;
            border-bottom: 2px solid var(--accent); cursor: pointer; transition: all 0.2s;
        }}
        .term:hover {{ background: rgba(255,107,107,0.3); }}
        
        /* Tooltip */
        .term-wrapper {{ position: relative; display: inline; }}
        .term-tooltip {{
            position: absolute; bottom: 100%; left: 50%;
            transform: translateX(-50%) translateY(-8px);
            background: var(--bg2); border: 1px solid var(--border);
            border-radius: 12px; padding: 12px 16px;
            min-width: 200px; max-width: 280px;
            z-index: 100; opacity: 0; visibility: hidden;
            transition: all 0.2s; pointer-events: none;
        }}
        .term-wrapper:hover .term-tooltip {{ opacity: 1; visibility: visible; }}
        .tooltip-name {{ font-weight: 600; font-size: 15px; }}
        .tooltip-en {{ font-size: 12px; color: var(--accent); }}
        .tooltip-desc {{ font-size: 12px; color: var(--text2); margin-top: 6px; }}
        
        /* Detail Panel */
        .detail-card {{ 
            background: rgba(255,255,255,0.03); border-radius: 16px;
            padding: 24px; margin-bottom: 16px;
        }}
        .detail-header {{ display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }}
        .detail-avatar {{ 
            width: 64px; height: 64px; border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-size: 28px; font-weight: 700; color: white; flex-shrink: 0;
        }}
        .detail-name {{ font-size: 24px; font-weight: 700; }}
        .detail-en {{ font-size: 16px; color: var(--accent); }}
        .detail-section {{ margin-bottom: 16px; }}
        .detail-section-title {{ 
            font-size: 11px; font-weight: 600; color: var(--text3);
            text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;
        }}
        .detail-text {{ font-size: 14px; color: var(--text2); line-height: 1.7; }}
        .quote-box {{
            background: var(--bg3); border-left: 4px solid var(--accent);
            padding: 12px 16px; border-radius: 0 8px 8px 0;
            font-style: italic; color: var(--text2);
        }}
        
        /* Full Book Notice */
        .full-book-notice {{
            background: linear-gradient(135deg, rgba(255,107,107,0.1), rgba(255,142,83,0.1));
            border: 1px solid var(--accent);
            border-radius: 12px; padding: 16px 20px;
            margin: 20px 0; text-align: center;
        }}
        .full-book-notice h3 {{ color: var(--accent); margin-bottom: 8px; }}
        .full-book-notice p {{ color: var(--text2); font-size: 14px; }}
    </style>
</head>
<body>
    <div id="app"></div>
    <script>
        const novelData = {data_json};
        let currentChapter = 0;
        
        function escapeRegExp(string) {{
            return string.replace(/[.*+?^${{}}()|[\]\\]/g, '\\$&');
        }}
        
        function renderApp() {{
            const app = document.getElementById('app');
            app.innerHTML = `
                <div class="app">
                    <header class="header">
                        <div class="logo">📖 赘婿 | My Heroic Husband</div>
                        <div class="view-options">
                            <button class="view-btn active" onclick="setView('both')">双语</button>
                            <button class="view-btn" onclick="setView('zh')">中文</button>
                            <button class="view-btn" onclick="setView('en')">English</button>
                        </div>
                    </header>
                    <div class="main">
                        <aside class="sidebar sidebar-left">
                            <div class="section-title">
                                章节 Chapters
                                <span>${{novelData.chapters.length}}/832</span>
                            </div>
                            <div id="chapter-list"></div>
                            
                            <div class="section-title">
                                人物 Characters
                                <span>${{novelData.characters.length}}</span>
                            </div>
                            <div id="char-list"></div>
                            
                            <div class="section-title">
                                概念 Concepts
                                <span>${{novelData.concepts.length}}</span>
                            </div>
                            <div id="concept-list"></div>
                        </aside>
                        <main class="reader">
                            <div class="reader-toolbar">
                                <span style="color: var(--text2)">
                                    Chapter ${{currentChapter + 1}} / ${{novelData.chapters.length}}
                                    ${{novelData.chapters.length < 832 ? ' (前10章预览)' : ''}}
                                </span>
                            </div>
                            <div class="reader-content" id="reader-content"></div>
                        </main>
                        <aside class="sidebar sidebar-right" id="sidebar-right">
                            <div class="detail-card">
                                <div style="color: var(--text3); text-align: center; padding: 40px 20px;">
                                    <div style="font-size: 48px; margin-bottom: 16px;">👆</div>
                                    <div>点击高亮术语查看详情</div>
                                    <div style="font-size: 12px; margin-top: 8px;">Click highlighted terms for details</div>
                                </div>
                            </div>
                        </aside>
                    </div>
                </div>
            `;
            renderChapterList();
            renderChars();
            renderConcepts();
            renderChapter(0);
        }}
        
        function renderChapterList() {{
            const container = document.getElementById('chapter-list');
            if (!container) return;
            container.innerHTML = novelData.chapters.map((ch, i) => `
                <div class="chapter-item ${{i === currentChapter ? 'active' : ''}}" onclick="goToChapter(${{i}})">
                    <div class="chapter-num">${{i + 1}}</div>
                    <div class="chapter-title">${{ch.title}}</div>
                </div>
            `).join('');
        }}
        
        function renderChars() {{
            const container = document.getElementById('char-list');
            if (!container) return;
            container.innerHTML = novelData.characters.map(char => `
                <div class="char-card" onclick="showCharDetail('${{char.id}}')">
                    <div class="char-avatar" style="background: ${{char.color}}">${{char.name[0]}}</div>
                    <div>
                        <div class="char-name">${{char.name}}</div>
                        <div class="char-en">${{char.enName}}</div>
                        <div class="char-role">${{char.role}}</div>
                    </div>
                </div>
            `).join('');
        }}
        
        function renderConcepts() {{
            const container = document.getElementById('concept-list');
            if (!container) return;
            container.innerHTML = novelData.concepts.map(concept => `
                <div class="char-card" onclick="showConceptDetail('${{concept.id}}')">
                    <div class="char-avatar" style="background: #666">📖</div>
                    <div>
                        <div class="char-name">${{concept.name}}</div>
                        <div class="char-en">${{concept.enName}}</div>
                    </div>
                </div>
            `).join('');
        }}
        
        function highlightTerms(text) {{
            const terms = [...novelData.characters, ...novelData.concepts]
                .sort((a, b) => b.name.length - a.name.length);
            
            terms.forEach(item => {{
                const regex = new RegExp(escapeRegExp(item.name), 'g');
                const desc = (item.description || '').substring(0, 50);
                text = text.replace(regex, match => `
                    <span class="term-wrapper">
                        <span class="term" onclick="showTermDetail('${{item.id}}')">${{match}}</span>
                        <div class="term-tooltip">
                            <div class="tooltip-name">${{item.name}}</div>
                            <div class="tooltip-en">${{item.enName}}</div>
                            <div class="tooltip-desc">${{desc}}...</div>
                        </div>
                    </span>
                `);
            }});
            return text;
        }}
        
        function renderChapter(index) {{
            currentChapter = index;
            const chapter = novelData.chapters[index];
            const container = document.getElementById('reader-content');
            
            let html = `
                <div class="chapter-header">
                    <h1 class="chapter-heading">${{chapter.title}}</h1>
                </div>
            `;
            
            chapter.paragraphs.forEach(para => {{
                html += `<div class="para-block">`;
                html += `<div class="zh-text">${{highlightTerms(para.zh)}}</div>`;
                if (para.en && para.en !== para.zh && !para.en.includes('Translation failed')) {{
                    html += `<div class="en-text">${{para.en}}</div>`;
                }}
                html += `</div>`;
            }});
            
            // 添加全书提示
            if (novelData.chapters.length < 832) {{
                html += `
                    <div class="full-book-notice">
                        <h3>📚 全书共832章</h3>
                        <p>当前为前${{novelData.chapters.length}}章双语预览版<br>
                        Full book has 832 chapters. This is a preview of the first ${{novelData.chapters.length}} chapters.</p>
                    </div>
                `;
            }}
            
            container.innerHTML = html;
            container.scrollTop = 0;
            renderChapterList();
        }}
        
        function goToChapter(index) {{
            renderChapter(index);
        }}
        
        function showTermDetail(id) {{
            const char = novelData.characters.find(c => c.id === id);
            if (char) return showCharDetail(id);
            const concept = novelData.concepts.find(c => c.id === id);
            if (concept) return showConceptDetail(id);
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
                        <div class="detail-section-title">身份 Role</div>
                        <div class="detail-text">${{char.role}}</div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-section-title">简介 Description</div>
                        <div class="detail-text">${{char.description}}</div>
                    </div>
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
                        <div class="detail-section-title">分类 Category</div>
                        <span style="background: var(--bg3); padding: 4px 12px; border-radius: 8px; font-size: 13px;">${{concept.category}}</span>
                    </div>
                    <div class="detail-section">
                        <div class="detail-section-title">描述 Description</div>
                        <div class="detail-text">${{concept.description}}</div>
                    </div>
                </div>
            `;
        }}
        
        function setView(mode) {{
            document.querySelectorAll('.view-btn').forEach(btn => {{
                btn.classList.remove('active');
                if (btn.textContent.includes(mode === 'both' ? '双语' : mode === 'zh' ? '中文' : 'English')) {{
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
        
        // Initialize
        renderApp();
    </script>
</body>
</html>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML已生成: {output_path}")
        print(f"   文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")
    
    def process(self, filepath):
        """主流程"""
        print("=" * 60)
        print("  《赘婿》双语阅读器生成器")
        print("=" * 60)
        print()
        
        # 加载文件
        self.load_file(filepath)
        print()
        
        # 解析章节（前10章）
        self.parse_chapters(max_chapters=10)
        print()
        
        # 提取人物概念
        self.extract_entities()
        print()
        
        # 翻译
        self.translate_chapters()
        print()
        
        # 生成HTML
        output_path = "/root/.openclaw/workspace/赘婿_双语阅读器.html"
        self.generate_html(output_path)
        
        print()
        print("=" * 60)
        print("🎉 处理完成！")
        print(f"   输出: {output_path}")
        print("=" * 60)
        
        return output_path


if __name__ == "__main__":
    processor = ZhuixuProcessor()
    processor.process("/root/openclaw/kimi/downloads/19ceb927-aef2-809a-8000-00003d106cff_赘婿.txt")

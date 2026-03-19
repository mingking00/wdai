#!/usr/bin/env python3
"""
翻译大师智能体 - Translation Master Agent
使用方法: 把TXT文件拖到这个脚本上，自动生成双语阅读器
"""

import os
import sys
import re
import json
import time
from pathlib import Path

# ============ 配置区域 ============
# 默认使用本地模型（免费），如需云端API请取消下面注释并填入Key

# API_CONFIG = {
#     "api_key": "你的Kimi API Key",
#     "base_url": "https://api.moonshot.cn/v1",
#     "model": "moonshot-v1-8k"
# }

API_CONFIG = None  # 使用本地模型

# ===================================

class TranslationMaster:
    """翻译大师智能体 - 全自动双语处理"""
    
    def __init__(self):
        self.novel_data = {
            "title": "",
            "chapters": [],
            "characters": [],
            "concepts": []
        }
        self.api_config = API_CONFIG
        
    def log(self, emoji, message):
        """打印日志"""
        print(f"{emoji} {message}")
        
    def call_ai(self, prompt, system="你是一个专业的文学翻译助手"):
        """调用AI - 自动选择本地或云端"""
        if self.api_config:
            return self._call_cloud_api(prompt, system)
        else:
            return self._call_local_model(prompt, system)
    
    def _call_cloud_api(self, prompt, system):
        """调用云端API (Kimi/OpenAI)"""
        try:
            import requests
            headers = {
                'Authorization': f"Bearer {self.api_config['api_key']}",
                'Content-Type': 'application/json'
            }
            payload = {
                'model': self.api_config['model'],
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3
            }
            response = requests.post(
                f"{self.api_config['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            self.log("❌", f"云端API调用失败: {e}")
            return None
    
    def _call_local_model(self, prompt, system):
        """调用本地Ollama模型"""
        try:
            import requests
            payload = {
                "model": "llama3.1",
                "prompt": f"{system}\n\n{prompt}",
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 2048}
            }
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=300
            )
            return response.json().get('response', '')
        except Exception as e:
            self.log("❌", f"本地模型调用失败: {e}")
            return None
    
    def check_environment(self):
        """检查运行环境"""
        if self.api_config:
            self.log("☁️", "使用云端API模式")
            return True
        
        # 检查本地Ollama
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                self.log("🖥️", "使用本地Ollama模型 (llama3.1)")
                return True
        except:
            pass
        
        self.log("⚠️", "未检测到AI服务")
        print("""
请选择运行模式:
1. 使用云端API (需要Kimi/OpenAI Key) - 输入 'cloud'
2. 使用本地模型 (需要安装Ollama) - 输入 'local'
        """)
        choice = input("选择 (cloud/local): ").strip().lower()
        
        if choice == 'cloud':
            key = input("请输入API Key: ").strip()
            self.api_config = {
                "api_key": key,
                "base_url": "https://api.moonshot.cn/v1",
                "model": "moonshot-v1-8k"
            }
            return True
        else:
            print("""
请安装Ollama:
1. 访问 https://ollama.com 下载安装
2. 运行: ollama pull llama3.1
3. 重新运行此脚本
            """)
            return False
    
    def analyze_structure(self, text):
        """Step 1: 分析小说结构"""
        self.log("📖", "正在分析小说结构...")
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        title = lines[0] if lines else "Unknown Novel"
        if len(title) > 50:
            title = "Unknown Novel"
        
        # 智能章节检测
        chapter_patterns = [
            r'^第[一二三四五六七八九十百千万\d]+章',
            r'^Chapter\s*\d+',
            r'^\d+\s*[、\.．]',
            r'^【[^】]+】',
            r'^\[[^\]]+\]'
        ]
        
        chapters = []
        current_chapter = {"title": "序章", "content": []}
        
        for line in lines[1:]:
            is_chapter = any(re.match(p, line, re.IGNORECASE) for p in chapter_patterns)
            
            if is_chapter and len(line) < 100:
                if current_chapter["content"]:
                    chapters.append(current_chapter)
                current_chapter = {"title": line, "content": []}
            elif len(line) > 20:
                current_chapter["content"].append(line)
        
        if current_chapter["content"]:
            chapters.append(current_chapter)
        
        # 如果没检测到章节，自动分段
        if len(chapters) <= 1 and len(lines) > 50:
            paragraphs = [l for l in lines if len(l) > 20]
            chunk_size = max(10, len(paragraphs) // 10)
            chapters = []
            for i in range(0, len(paragraphs), chunk_size):
                chunk = paragraphs[i:i+chunk_size]
                if chunk:
                    chapters.append({
                        "title": f"第{i//chunk_size + 1}章",
                        "content": chunk
                    })
        
        self.novel_data["title"] = title
        self.novel_data["chapters"] = chapters
        self.log("✅", f"发现 {len(chapters)} 个章节，共 {sum(len(c['content']) for c in chapters)} 段")
        return chapters
    
    def extract_entities(self):
        """Step 2: 提取人物和概念"""
        self.log("🔍", "正在提取人物和概念...")
        
        # 收集样本（前5章，每章前3段）
        samples = []
        for ch in self.novel_data["chapters"][:5]:
            for para in ch["content"][:3]:
                if len(para) > 30:
                    samples.append(para)
        
        sample_text = '\n\n'.join(samples[:15])
        
        prompt = f"""分析这段中文小说，提取关键术语。

严格按以下JSON格式返回:
{{
  "characters": [
    {{"name": "中文名", "enName": "拼音", "role": "身份", "description": "一句话描述"}}
  ],
  "concepts": [
    {{"name": "中文名", "enName": "English", "category": "地点/组织/物品/概念", "description": "描述"}}
  ]
}}

小说内容:
{sample_text[:2500]}

只返回JSON，不要其他内容。"""

        result = self.call_ai(prompt)
        if not result:
            self.log("⚠️", "术语提取失败，继续处理")
            return
        
        try:
            # 提取JSON
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group())
                
                colors = ['#E74C3C', '#3498DB', '#27AE60', '#9B59B6', '#F39C12', '#1ABC9C']
                
                for i, char in enumerate(data.get('characters', [])):
                    self.novel_data['characters'].append({
                        "id": f"char_{i}",
                        "name": char['name'],
                        "enName": char.get('enName', char['name']),
                        "role": char.get('role', 'Character'),
                        "description": char.get('description', ''),
                        "color": colors[i % len(colors)],
                        "quote": ""
                    })
                
                for i, concept in enumerate(data.get('concepts', [])):
                    self.novel_data['concepts'].append({
                        "id": f"concept_{i}",
                        "name": concept['name'],
                        "enName": concept.get('enName', concept['name']),
                        "category": concept.get('category', 'Concept'),
                        "description": concept.get('description', ''),
                        "importance": ""
                    })
                
                self.log("✅", f"提取了 {len(self.novel_data['characters'])} 个人物，{len(self.novel_data['concepts'])} 个概念")
        except Exception as e:
            self.log("⚠️", f"术语解析失败: {e}")
    
    def translate_content(self):
        """Step 3: 翻译内容"""
        total_chapters = len(self.novel_data['chapters'])
        self.log("🌐", f"开始翻译 {total_chapters} 个章节...")
        
        for idx, chapter in enumerate(self.novel_data['chapters']):
            progress = (idx + 1) / total_chapters * 100
            print(f"   ⏳ 第 {idx+1}/{total_chapters} 章 ({progress:.0f}%)", end='\r')
            
            chapter['paragraphs'] = []
            
            # 每章最多翻译前10段（演示模式）
            for para in chapter['content'][:10]:
                if len(para) < 10:
                    chapter['paragraphs'].append({'zh': para, 'en': para})
                    continue
                
                prompt = f"""将以下中文翻译成流畅自然的英文：

要求：
1. 保持文学性和流畅度
2. 人名用地道拼音（如：张三 → Zhang San）
3. 只返回翻译结果，不要解释

中文：
{para}

英文："""
                
                result = self.call_ai(prompt)
                if result:
                    chapter['paragraphs'].append({
                        'zh': para,
                        'en': result.strip()
                    })
                else:
                    chapter['paragraphs'].append({
                        'zh': para,
                        'en': '[翻译失败]'
                    })
                
                time.sleep(0.2)  # 避免限流
        
        print()  # 换行
        self.log("✅", "翻译完成")
    
    def generate_output(self, output_path):
        """Step 4: 生成HTML"""
        self.log("🎨", "正在生成交互式阅读器...")
        
        data_json = json.dumps(self.novel_data, ensure_ascii=False)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.novel_data['title']} - 双语阅读器</title>
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
        .main {{ display: grid; grid-template-columns: 280px 1fr 320px; overflow: hidden; }}
        
        /* Sidebar */
        .sidebar {{ background: var(--bg2); padding: 20px; overflow-y: auto; }}
        .sidebar-left {{ border-right: 1px solid var(--border); }}
        .sidebar-right {{ border-left: 1px solid var(--border); }}
        .section-title {{ 
            font-size: 11px; font-weight: 600; color: var(--text3);
            text-transform: uppercase; letter-spacing: 0.5px;
            margin-bottom: 12px; display: flex; justify-content: space-between;
        }}
        .section-title span {{ background: var(--bg3); padding: 2px 8px; border-radius: 12px; }}
        
        /* Chapter List */
        .chapter-item {{ 
            display: flex; align-items: center; gap: 12px;
            padding: 12px; border-radius: 10px; cursor: pointer;
            margin-bottom: 4px; transition: all 0.2s;
        }}
        .chapter-item:hover {{ background: rgba(255,255,255,0.05); }}
        .chapter-item.active {{ background: var(--bg3); }}
        .chapter-num {{ 
            width: 28px; height: 28px; border-radius: 8px;
            background: var(--bg3); display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: 600; color: var(--text3);
        }}
        .chapter-item.active .chapter-num {{ background: var(--accent); color: white; }}
        
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
            font-size: 18px; font-weight: 700; color: white;
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
            background: transparent; color: var(--text3); font-size: 13px; cursor: pointer;
        }}
        .view-btn.active {{ background: rgba(255,255,255,0.1); color: var(--text); }}
        .reader-content {{ flex: 1; overflow-y: auto; padding: 40px 48px; }}
        
        /* Content */
        .chapter-header {{ margin-bottom: 40px; padding-bottom: 24px; border-bottom: 1px solid var(--border); }}
        .chapter-heading {{ 
            font-size: 32px; font-weight: 700;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }}
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
            border-bottom: 2px solid var(--accent); cursor: pointer;
        }}
        .term:hover {{ background: rgba(255,107,107,0.3); }}
        
        /* Detail Panel */
        .detail-card {{ 
            background: rgba(255,255,255,0.03); border-radius: 16px;
            padding: 24px; margin-bottom: 16px;
        }}
        .detail-header {{ display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }}
        .detail-avatar {{ 
            width: 64px; height: 64px; border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-size: 28px; font-weight: 700; color: white;
        }}
        .detail-name {{ font-size: 24px; font-weight: 700; }}
        .detail-en {{ font-size: 16px; color: var(--accent); }}
        .detail-section {{ margin-bottom: 16px; }}
        .detail-section-title {{ 
            font-size: 11px; font-weight: 600; color: var(--text3);
            text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;
        }}
        .detail-text {{ font-size: 14px; color: var(--text2); line-height: 1.7; }}
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
                        <div class="logo">📖 ${{novelData.title}}</div>
                        <div class="view-options">
                            <button class="view-btn active" onclick="setView('both')">双语</button>
                            <button class="view-btn" onclick="setView('zh')">中文</button>
                            <button class="view-btn" onclick="setView('en')">English</button>
                        </div>
                    </header>
                    <div class="main">
                        <aside class="sidebar sidebar-left">
                            <div class="section-title">章节 <span>${{novelData.chapters.length}}</span></div>
                            <div id="chapter-list"></div>
                            ${{novelData.characters.length ? `
                            <div class="section-title">人物 <span>${{novelData.characters.length}}</span></div>
                            <div id="char-list"></div>
                            ` : ''}}
                            ${{novelData.concepts.length ? `
                            <div class="section-title">概念 <span>${{novelData.concepts.length}}</span></div>
                            <div id="concept-list"></div>
                            ` : ''}}
                        </aside>
                        <main class="reader">
                            <div class="reader-toolbar">
                                <span style="color: var(--text3)">Chapter ${{currentChapter + 1}} / ${{novelData.chapters.length}}</span>
                            </div>
                            <div class="reader-content" id="reader-content"></div>
                        </main>
                        <aside class="sidebar sidebar-right" id="sidebar-right">
                            <div class="detail-card">
                                <div style="color: var(--text3); text-align: center;">
                                    点击高亮术语查看详情
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
                    <div style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${{ch.title}}</div>
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
                text = text.replace(regex, `<span class="term" onclick="showTermDetail('${{item.id}}')">${{item.name}}</span>`);
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
                if (para.en && para.en !== para.zh && !para.en.includes('翻译失败')) {{
                    html += `<div class="en-text">${{para.en}}</div>`;
                }}
                html += `</div>`;
            }});
            
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
                        <div class="detail-section-title">身份</div>
                        <div class="detail-text">${{char.role}}</div>
                    </div>
                    <div class="detail-section">
                        <div class="detail-section-title">简介</div>
                        <div class="detail-text">${{char.description || '暂无描述'}}</div>
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
                        <div class="detail-section-title">分类</div>
                        <span style="background: var(--bg3); padding: 4px 12px; border-radius: 8px; font-size: 13px;">${{concept.category}}</span>
                    </div>
                    <div class="detail-section">
                        <div class="detail-section-title">描述</div>
                        <div class="detail-text">${{concept.description || '暂无描述'}}</div>
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
        
        renderApp();
    </script>
</body>
</html>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.log("✅", f"已生成: {output_path}")
        return output_path
    
    def process(self, txt_path):
        """主处理流程"""
        self.log("🚀", "翻译大师智能体启动")
        print("=" * 60)
        
        # 检查环境
        if not self.check_environment():
            return False
        
        # 读取文件
        self.log("📖", f"读取: {txt_path}")
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        self.log("📊", f"文本长度: {len(text)} 字符")
        
        # 执行四步流程
        print()
        self.analyze_structure(text)
        print()
        self.extract_entities()
        print()
        self.translate_content()
        print()
        
        # 生成输出
        output_name = Path(txt_path).stem + "_双语版.html"
        output_path = os.path.join(os.path.dirname(txt_path) or '.', output_name)
        self.generate_output(output_path)
        
        print()
        print("=" * 60)
        self.log("🎉", "处理完成！")
        print(f"   输出文件: {output_path}")
        print(f"   章节数: {len(self.novel_data['chapters'])}")
        print(f"   人物: {len(self.novel_data['characters'])}")
        print(f"   概念: {len(self.novel_data['concepts'])}")
        print("=" * 60)
        return True


def main():
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════╗
║           翻译大师智能体 - Translation Master            ║
╚══════════════════════════════════════════════════════════╝

使用方法:
  python translation_master.py <小说.txt>

或者直接把TXT文件拖到这个脚本上

输出: 同名_双语版.html (可直接双击打开)
        """)
        # 交互式输入
        txt_path = input("\n请输入小说文件路径: ").strip().strip('"')
    else:
        txt_path = sys.argv[1]
    
    if not os.path.exists(txt_path):
        print(f"❌ 文件不存在: {txt_path}")
        sys.exit(1)
    
    # 创建智能体并运行
    master = TranslationMaster()
    master.process(txt_path)


if __name__ == "__main__":
    main()

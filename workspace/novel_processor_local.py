#!/usr/bin/env python3
"""
Vibero Novel Processor - Local Mode
使用本地Ollama模型，无需API Key
"""

import re
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装依赖: pip install requests")
    sys.exit(1)

class LocalNovelProcessor:
    """使用本地Ollama模型处理小说"""
    
    def __init__(self, model="llama3.1", ollama_url="http://localhost:11434"):
        self.model = model
        self.ollama_url = ollama_url
        self.novel_data = {
            "title": "",
            "chapters": [],
            "characters": [],
            "concepts": []
        }
    
    def check_ollama(self):
        """检查Ollama是否运行"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def call_local_ai(self, prompt, system=""):
        """调用本地Ollama模型"""
        payload = {
            "model": self.model,
            "prompt": f"{system}\n\n{prompt}" if system else prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 2048
            }
        }
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            print(f"❌ 本地模型调用失败: {e}")
            return None
    
    def parse_novel(self, text):
        """解析小说结构"""
        print("📖 分析小说结构...")
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        title = lines[0] if lines else "Unknown Novel"
        if len(title) > 50:
            title = "Unknown Novel"
        
        # 简单分章
        chapter_pattern = r'^(第[一二三四五六七八九十百千万\d]+章|Chapter\s*\d+)'
        chapters = []
        current_chapter = {"title": "序章", "content": []}
        
        for line in lines[1:]:
            if re.match(chapter_pattern, line, re.IGNORECASE) and len(line) < 100:
                if current_chapter["content"]:
                    chapters.append(current_chapter)
                current_chapter = {"title": line, "content": []}
            elif len(line) > 20:
                current_chapter["content"].append(line)
        
        if current_chapter["content"]:
            chapters.append(current_chapter)
        
        if len(chapters) == 0:
            paragraphs = [l for l in lines if len(l) > 20]
            for i in range(0, min(len(paragraphs), 100), 10):
                chapters.append({
                    "title": f"第{i//10 + 1}部分",
                    "content": paragraphs[i:i+10]
                })
        
        self.novel_data["title"] = title
        self.novel_data["chapters"] = chapters
        print(f"✅ 发现 {len(chapters)} 个章节")
        return chapters
    
    def extract_terms(self):
        """使用本地模型提取术语"""
        print("🔍 提取人物和概念（使用本地模型，较慢）...")
        
        # 只取前5章作为样本
        samples = []
        for ch in self.novel_data["chapters"][:5]:
            for para in ch["content"][:3]:
                if len(para) > 30:
                    samples.append(para)
        
        sample = '\n'.join(samples[:10])
        
        prompt = f"""分析这段中文小说，提取关键术语。

格式要求（严格JSON）：
{{
  "characters": [{{"name": "中文名", "enName": "Pinyin", "role": "身份", "description": "描述"}}],
  "concepts": [{{"name": "中文名", "enName": "English", "category": "人物/地点/组织/概念", "description": "描述"}}]
}}

小说内容：
{sample[:2000]}

只返回JSON，不要其他内容："""

        result = self.call_local_ai(prompt)
        if not result:
            return
        
        try:
            # 提取JSON
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group())
                
                for i, char in enumerate(data.get('characters', [])):
                    self.novel_data['characters'].append({
                        "id": f"char_{i}",
                        "name": char['name'],
                        "enName": char.get('enName', char['name']),
                        "role": char.get('role', 'Character'),
                        "description": char.get('description', ''),
                        "color": self._get_color(i),
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
                
                print(f"✅ 提取了 {len(self.novel_data['characters'])} 个人物，{len(self.novel_data['concepts'])} 个概念")
        except Exception as e:
            print(f"⚠️ 术语解析失败: {e}")
    
    def _get_color(self, index):
        colors = ['#E74C3C', '#3498DB', '#27AE60', '#9B59B6', '#F39C12']
        return colors[index % len(colors)]
    
    def translate_chapters(self):
        """翻译章节（本地模型很慢）"""
        print("🌐 开始翻译（本地模型较慢，请耐心）...")
        print("💡 提示：只翻译前3章作为演示，完整翻译建议用云端API")
        
        for ch_idx, chapter in enumerate(self.novel_data['chapters'][:3]):  # 只翻译前3章
            print(f"  翻译第 {ch_idx+1} 章...")
            chapter['paragraphs'] = []
            
            for para in chapter['content'][:5]:  # 每章只翻译前5段
                if len(para) < 10:
                    chapter['paragraphs'].append({'zh': para, 'en': para})
                    continue
                
                prompt = f"""Translate this Chinese to English:

{para}

English:"""
                
                result = self.call_local_ai(prompt)
                if result:
                    chapter['paragraphs'].append({
                        'zh': para,
                        'en': result.strip()
                    })
                else:
                    chapter['paragraphs'].append({
                        'zh': para,
                        'en': '[Translation failed]'
                    })
        
        # 其余章节保留原文
        for ch in self.novel_data['chapters'][3:]:
            ch['paragraphs'] = [{'zh': p, 'en': '[Not translated in demo]'} for p in ch['content']]
        
        print("✅ 翻译完成（演示模式：前3章）")
    
    def generate_html(self, output_path):
        """生成HTML"""
        print("🎨 生成HTML...")
        
        # 使用内嵌数据生成HTML（代码同之前）
        data_json = json.dumps(self.novel_data, ensure_ascii=False)
        
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{self.novel_data['title']} - Bilingual Reader</title>
    <style>
        :root {{ --bg: #0a0a0f; --bg2: #12121a; --accent: #ff6b6b; --text: #fff; --text2: #a0a0b0; }}
        body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; height: 100vh; overflow: hidden; }}
        .app {{ display: grid; grid-template-rows: 60px 1fr; height: 100vh; }}
        .header {{ display: flex; align-items: center; justify-content: space-between; padding: 0 24px; background: var(--bg2); border-bottom: 1px solid rgba(255,255,255,0.08); }}
        .logo {{ font-size: 20px; font-weight: bold; background: linear-gradient(135deg, #ff6b6b, #ff8e53); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .main {{ display: grid; grid-template-columns: 280px 1fr 320px; overflow: hidden; }}
        .sidebar {{ background: var(--bg2); padding: 20px; overflow-y: auto; }}
        .sidebar-left {{ border-right: 1px solid rgba(255,255,255,0.08); }}
        .sidebar-right {{ border-left: 1px solid rgba(255,255,255,0.08); }}
        .section-title {{ font-size: 12px; color: #606070; text-transform: uppercase; margin-bottom: 12px; display: flex; justify-content: space-between; }}
        .chapter-item {{ padding: 12px; border-radius: 8px; cursor: pointer; margin-bottom: 4px; font-size: 14px; display: flex; gap: 12px; }}
        .chapter-item:hover {{ background: rgba(255,255,255,0.05); }}
        .chapter-item.active {{ background: rgba(255,255,255,0.08); }}
        .chapter-num {{ width: 28px; height: 28px; border-radius: 8px; background: #1a1a28; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; }}
        .chapter-item.active .chapter-num {{ background: var(--accent); }}
        .char-card {{ display: flex; gap: 12px; padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.03); cursor: pointer; margin-bottom: 8px; }}
        .char-card:hover {{ background: rgba(255,255,255,0.06); }}
        .char-avatar {{ width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; color: white; }}
        .char-name {{ font-weight: 600; }}
        .char-en {{ font-size: 12px; color: var(--text2); }}
        .reader {{ display: flex; flex-direction: column; overflow: hidden; }}
        .reader-toolbar {{ padding: 16px 32px; border-bottom: 1px solid rgba(255,255,255,0.08); background: var(--bg2); display: flex; justify-content: space-between; }}
        .reader-content {{ flex: 1; overflow-y: auto; padding: 40px; }}
        .chapter-heading {{ font-size: 32px; font-weight: bold; background: linear-gradient(135deg, #ff6b6b, #ff8e53); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .para-block {{ margin-bottom: 32px; padding: 20px; border-radius: 16px; background: rgba(255,255,255,0.03); }}
        .zh-text {{ font-size: 17px; line-height: 1.8; margin-bottom: 12px; }}
        .en-text {{ font-size: 15px; color: var(--text2); padding-left: 16px; border-left: 3px solid var(--accent); }}
        .term {{ background: rgba(255,107,107,0.2); padding: 2px 8px; border-radius: 6px; cursor: pointer; border-bottom: 2px solid var(--accent); }}
        .detail-card {{ background: rgba(255,255,255,0.03); border-radius: 16px; padding: 24px; margin-bottom: 20px; }}
        .detail-avatar {{ width: 64px; height: 64px; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; color: white; margin-bottom: 16px; }}
        .detail-name {{ font-size: 24px; font-weight: bold; }}
        .detail-en {{ color: var(--accent); }}
        button {{ padding: 8px 16px; border-radius: 8px; border: none; background: rgba(255,255,255,0.08); color: var(--text2); cursor: pointer; }}
        button.active {{ background: rgba(255,255,255,0.12); color: white; }}
    </style>
</head>
<body>
    <div id="app"></div>
    <script>
        const novelData = {data_json};
        let currentChapter = 0;
        
        function renderApp() {{
            const app = document.getElementById('app');
            app.innerHTML = `
                <div class="app">
                    <header class="header">
                        <div class="logo">📖 ${{novelData.title}}</div>
                        <div>
                            <button class="active" onclick="setView('both')">双语</button>
                            <button onclick="setView('zh')">中文</button>
                            <button onclick="setView('en')">English</button>
                        </div>
                    </header>
                    <div class="main">
                        <aside class="sidebar sidebar-left">
                            <div class="section-title">章节 <span>${{novelData.chapters.length}}</span></div>
                            <div id="chapter-list"></div>
                            ${{novelData.characters.length ? `<div class="section-title">人物 <span>${{novelData.characters.length}}</span></div>` : ''}}
                            <div id="char-list"></div>
                            ${{novelData.concepts.length ? `<div class="section-title">概念 <span>${{novelData.concepts.length}}</span></div>` : ''}}
                            <div id="concept-list"></div>
                        </aside>
                        <main class="reader">
                            <div class="reader-toolbar">
                                <span style="color: var(--text2)">Chapter ${{currentChapter + 1}} / ${{novelData.chapters.length}}</span>
                            </div>
                            <div class="reader-content" id="reader-content"></div>
                        </main>
                        <aside class="sidebar sidebar-right" id="sidebar-right">
                            <div class="detail-card">
                                <div style="color: var(--text2)">Click on highlighted terms</div>
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
            document.getElementById('chapter-list').innerHTML = novelData.chapters.map((ch, i) => `
                <div class="chapter-item ${{i === currentChapter ? 'active' : ''}}" onclick="goToChapter(${{i}})">
                    <div class="chapter-num">${{i + 1}}</div>
                    <div style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${{ch.title}}</div>
                </div>
            `).join('');
        }}
        
        function renderChars() {{
            if (!novelData.characters.length) return;
            document.getElementById('char-list').innerHTML = novelData.characters.map(c => `
                <div class="char-card" onclick="showChar('${{c.id}}')">
                    <div class="char-avatar" style="background: ${{c.color}}">${{c.name[0]}}</div>
                    <div>
                        <div class="char-name">${{c.name}}</div>
                        <div class="char-en">${{c.enName}}</div>
                    </div>
                </div>
            `).join('');
        }}
        
        function renderConcepts() {{
            if (!novelData.concepts.length) return;
            document.getElementById('concept-list').innerHTML = novelData.concepts.map(c => `
                <div class="char-card" onclick="showConcept('${{c.id}}')">
                    <div class="char-avatar" style="background: #666">📖</div>
                    <div>
                        <div class="char-name">${{c.name}}</div>
                        <div class="char-en">${{c.enName}}</div>
                    </div>
                </div>
            `).join('');
        }}
        
        function highlightTerms(text) {{
            const terms = [...novelData.characters, ...novelData.concepts].sort((a, b) => b.name.length - a.name.length);
            terms.forEach(t => {{
                const re = new RegExp(t.name.replace(/[.*+?^${{}}()|[\]\\]/g, '\\$&'), 'g');
                text = text.replace(re, `<span class="term" onclick="showTerm('${{t.id}}')">${{t.name}}</span>`);
            }});
            return text;
        }}
        
        function renderChapter(idx) {{
            currentChapter = idx;
            const ch = novelData.chapters[idx];
            document.getElementById('reader-content').innerHTML = `
                <div style="margin-bottom: 40px;">
                    <h1 class="chapter-heading">${{ch.title}}</h1>
                </div>
                ${{ch.paragraphs.map(p => `
                    <div class="para-block">
                        <div class="zh-text">${{highlightTerms(p.zh)}}</div>
                        ${{p.en && p.en !== p.zh ? `<div class="en-text">${{p.en}}</div>` : ''}}
                    </div>
                `).join('')}}
            `;
            renderChapterList();
        }}
        
        function goToChapter(i) {{ renderChapter(i); }}
        
        function showTerm(id) {{
            const char = novelData.characters.find(c => c.id === id);
            if (char) return showChar(id);
            const concept = novelData.concepts.find(c => c.id === id);
            if (concept) return showConcept(id);
        }}
        
        function showChar(id) {{
            const c = novelData.characters.find(x => x.id === id);
            if (!c) return;
            document.getElementById('sidebar-right').innerHTML = `
                <div class="detail-card">
                    <div class="detail-avatar" style="background: ${{c.color}}">${{c.name[0]}}</div>
                    <div class="detail-name">${{c.name}}</div>
                    <div class="detail-en">${{c.enName}}</div>
                    <div style="margin-top: 16px; color: var(--text2);">${{c.role}}</div>
                    <div style="margin-top: 8px; color: var(--text2);">${{c.description}}</div>
                </div>
            `;
        }}
        
        function showConcept(id) {{
            const c = novelData.concepts.find(x => x.id === id);
            if (!c) return;
            document.getElementById('sidebar-right').innerHTML = `
                <div class="detail-card">
                    <div class="detail-avatar" style="background: #666">📖</div>
                    <div class="detail-name">${{c.name}}</div>
                    <div class="detail-en">${{c.enName}}</div>
                    <div style="margin-top: 8px; color: var(--text2);">${{c.description}}</div>
                </div>
            `;
        }}
        
        function setView(mode) {{
            document.querySelectorAll('button').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('.zh-text').forEach(el => el.style.display = mode === 'en' ? 'none' : 'block');
            document.querySelectorAll('.en-text').forEach(el => el.style.display = mode === 'zh' ? 'none' : 'block');
        }}
        
        renderApp();
    </script>
</body>
</html>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ 已保存: {output_path}")


def main():
    print("=" * 60)
    print("  Vibero Novel Processor - 本地模式（无需API）")
    print("=" * 60)
    print()
    
    # 检查Ollama
    processor = LocalNovelProcessor()
    if not processor.check_ollama():
        print("❌ Ollama 未运行")
        print()
        print("请先安装并启动 Ollama:")
        print("1. 访问 https://ollama.com 下载安装")
        print("2. 运行: ollama pull llama3.1")
        print("3. 运行: ollama serve")
        return
    
    print("✅ Ollama 已连接")
    print()
    
    # 获取文件
    txt_path = input("小说TXT路径: ").strip()
    if not os.path.exists(txt_path):
        print(f"❌ 文件不存在: {txt_path}")
        return
    
    # 读取
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"📖 读取: {len(text)} 字符")
    print()
    
    # 处理
    processor.parse_novel(text)
    processor.extract_terms()
    
    print()
    translate = input("是否翻译? (y/n，翻译较慢): ").strip().lower() == 'y'
    if translate:
        processor.translate_chapters()
    else:
        for ch in processor.novel_data['chapters']:
            ch['paragraphs'] = [{'zh': p, 'en': ''} for p in ch['content']]
    
    # 输出
    output = Path(txt_path).stem + "_local.html"
    processor.generate_html(output)
    print(f"\n✅ 完成: {output}")


if __name__ == "__main__":
    main()

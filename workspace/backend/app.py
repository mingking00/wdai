from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import json
import re
import os

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

# 配置
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# AI翻译函数
def translate_text(text, api_config):
    """调用AI API翻译文本"""
    if not api_config.get('api_key'):
        return None, "API密钥未配置"
    
    base_url = api_config.get('base_url', 'https://api.moonshot.cn/v1')
    model = api_config.get('model', 'moonshot-v1-8k')
    
    headers = {
        'Authorization': f"Bearer {api_config['api_key']}",
        'Content-Type': 'application/json'
    }
    
    prompt = f"""请将以下中文小说段落翻译成英文。要求：
1. 保持文学性和流畅度
2. 专有名词（人名、地名）使用拼音或保留中文
3. 只返回翻译结果，不要解释

中文原文：
{text}

英文翻译："""
    
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': '你是一个专业的小说翻译助手，擅长将中文小说翻译成流畅的英文。'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.3
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip(), None
    except Exception as e:
        return None, str(e)

def analyze_novel_structure(text):
    """分析小说结构"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # 检测章节
    chapter_pattern = r'^(第[一二三四五六七八九十百千万\d]+章|Chapter\s*\d+|\d+\s*\.)'
    chapters = []
    current_chapter = {'title': '序章', 'content': []}
    
    for line in lines:
        if re.match(chapter_pattern, line, re.IGNORECASE):
            if current_chapter['content']:
                chapters.append(current_chapter)
            current_chapter = {'title': line, 'content': []}
        elif len(line) > 10:
            current_chapter['content'].append(line)
    
    if current_chapter['content']:
        chapters.append(current_chapter)
    
    # 提取潜在人物名（2-4字的中文名）
    name_pattern = r'[\u4e00-\u9fa5]{2,4}'
    name_freq = {}
    for line in lines:
        for name in re.findall(name_pattern, line):
            if 2 <= len(name) <= 4:
                name_freq[name] = name_freq.get(name, 0) + 1
    
    # 过滤高频词作为人物
    characters = [
        {'name': name, 'count': count}
        for name, count in sorted(name_freq.items(), key=lambda x: -x[1])
        if count > 3
    ][:15]
    
    return {
        'chapters': chapters,
        'characters': characters,
        'total_paragraphs': sum(len(ch['content']) for ch in chapters)
    }

@app.route('/')
def index():
    """提供前端页面"""
    html_path = os.path.join(BASE_DIR, 'templates', 'index.html')
    return send_file(html_path)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """分析小说结构"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        text = file.read().decode('utf-8')
        result = analyze_novel_structure(text)
        result['filename'] = file.filename
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/translate', methods=['POST'])
def translate():
    """翻译文本"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    text = data.get('text', '')
    api_config = data.get('api_config', {})
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    translated, error = translate_text(text, api_config)
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify({'translation': translated})

@app.route('/api/translate-batch', methods=['POST'])
def translate_batch():
    """批量翻译"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    texts = data.get('texts', [])
    api_config = data.get('api_config', {})
    
    results = []
    for text in texts:
        translated, error = translate_text(text, api_config)
        results.append({
            'original': text,
            'translation': translated if not error else f'[Error: {error}]',
            'success': error is None
        })
    
    return jsonify({'results': results})

@app.route('/api/extract-terms', methods=['POST'])
def extract_terms():
    """提取关键术语"""
    data = request.json
    text = data.get('text', '')
    api_config = data.get('api_config', {})
    
    if not api_config.get('api_key'):
        return jsonify({'error': 'API key required'}), 400
    
    base_url = api_config.get('base_url', 'https://api.moonshot.cn/v1')
    model = api_config.get('model', 'moonshot-v1-8k')
    
    headers = {
        'Authorization': f"Bearer {api_config['api_key']}",
        'Content-Type': 'application/json'
    }
    
    prompt = f"""分析以下中文小说片段，提取关键术语（人名、地名、组织名、特殊概念）。
对每个术语提供：
1. 中文名
2. 英文翻译
3. 分类（人物/地点/组织/概念/历史事件）
4. 简短描述

返回JSON格式：
[{{"name": "术语中文", "enName": "English Name", "category": "分类", "description": "描述"}}]

小说片段：
{text[:2000]}"""
    
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': '你是一个专业的小说分析助手，擅长提取和翻译关键术语。'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.3
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # 提取JSON
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            terms = json.loads(json_match.group())
            return jsonify({'terms': terms})
        else:
            return jsonify({'error': 'Failed to parse terms'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 添加整书翻译接口
@app.route('/api/translate-book', methods=['POST'])
def translate_book():
    """翻译整本书（异步批量）"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    chapters = data.get('chapters', [])
    api_config = data.get('api_config', {})
    
    if not api_config.get('api_key'):
        return jsonify({'error': 'API key required'}), 400
    
    results = []
    total_paragraphs = sum(len(ch.get('paragraphs', [])) for ch in chapters)
    translated_count = 0
    
    for ch_idx, chapter in enumerate(chapters):
        ch_result = {
            'id': chapter.get('id', ch_idx),
            'paragraphs': []
        }
        
        for para_idx, para in enumerate(chapter.get('paragraphs', [])):
            zh_text = para.get('zh', '') if isinstance(para, dict) else para
            
            translated, error = translate_text(zh_text, api_config)
            ch_result['paragraphs'].append({
                'zh': zh_text,
                'en': translated if translated else f'[Error: {error}]'
            })
            
            translated_count += 1
            # 每翻译5段暂停一下，避免API限流
            if translated_count % 5 == 0:
                import time
                time.sleep(0.5)
        
        results.append(ch_result)
    
    return jsonify({
        'chapters': results,
        'total_paragraphs': total_paragraphs,
        'translated': translated_count
    })

# 添加整书术语提取接口
@app.route('/api/extract-book-terms', methods=['POST'])
def extract_book_terms():
    """从整本书提取关键术语"""
    data = request.json
    chapters = data.get('chapters', [])
    api_config = data.get('api_config', {})
    
    if not api_config.get('api_key'):
        return jsonify({'error': 'API key required'}), 400
    
    # 收集全书样本（每章取前3段，最多10章）
    sample_texts = []
    for ch in chapters[:10]:
        for para in ch.get('content', [])[:3]:
            if len(para) > 20:
                sample_texts.append(para)
    
    sample = '\n\n'.join(sample_texts[:15])
    
    base_url = api_config.get('base_url', 'https://api.moonshot.cn/v1')
    model = api_config.get('model', 'moonshot-v1-8k')
    
    headers = {
        'Authorization': f"Bearer {api_config['api_key']}",
        'Content-Type': 'application/json'
    }
    
    prompt = f"""分析以下中文小说内容，提取关键术语。

要求：
1. 提取主要人物（主角、重要配角）
2. 提取关键地点（城市、建筑、基地等）
3. 提取核心概念（组织、事件、技术、物品等）
4. 每个术语提供：中文名、英文名、分类、描述

分类只能是：人物/地点/组织/事件/概念/技术/物品

返回JSON格式：
[{{"name": "中文名", "enName": "English", "category": "人物/地点/组织/事件/概念/技术/物品", "description": "简短描述"}}]

小说内容：
{sample[:3000]}"""
    
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': '你是一个专业的小说分析助手，擅长提取和分类关键术语。'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.3
    }
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            terms = json.loads(json_match.group())
            return jsonify({'terms': terms})
        else:
            return jsonify({'error': 'Failed to parse terms'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':

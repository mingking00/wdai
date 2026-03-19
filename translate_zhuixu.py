import json
import requests
import time
import os

# 读取数据
with open('zhuixu_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# API配置
API_KEY = os.environ.get('KIMI_API_KEY', '')
if not API_KEY:
    print("⚠️ 未设置API Key，使用模拟翻译")
    use_mock = True
else:
    use_mock = False

headers = {
    'Authorization': f"Bearer {API_KEY}",
    'Content-Type': 'application/json'
}

def translate_text(text):
    """翻译单段文本"""
    if use_mock:
        return "[英文翻译将在此处显示]"
    
    if len(text) < 20:
        return text
    
    prompt = f"""将以下中文小说翻译成流畅自然的英文：

要求：
1. 保持文学性
2. 人名用拼音（宁毅→Ning Yi）
3. 只返回翻译结果

原文：{text}

英文："""
    
    try:
        response = requests.post(
            'https://api.moonshot.cn/v1/chat/completions',
            headers=headers,
            json={
                'model': 'moonshot-v1-8k',
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的小说翻译助手'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3
            },
            timeout=30
        )
        result = response.json()['choices'][0]['message']['content']
        return result.strip()
    except Exception as e:
        print(f"  翻译失败: {e}")
        return "[Translation failed]"

# 翻译每章的前10段
print("🌐 开始翻译前10章...")
for idx, chapter in enumerate(data['chapters']):
    print(f"\n第 {idx+1} 章: {chapter['title']}")
    chapter['paragraphs'] = []
    
    # 只翻译前10段
    for i, para in enumerate(chapter['content'][:10]):
        print(f"  翻译第 {i+1}/{min(10, len(chapter['content']))} 段...", end='\r')
        en = translate_text(para)
        chapter['paragraphs'].append({'zh': para, 'en': en})
        if not use_mock:
            time.sleep(0.5)
    
    print(f"  ✅ 完成 {len(chapter['paragraphs'])} 段翻译")

# 保存翻译后的数据
with open('zhuixu_translated.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n✅ 翻译完成，已保存到 zhuixu_translated.json")

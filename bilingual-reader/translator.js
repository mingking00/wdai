/**
 * 翻译器模块
 * 支持多种翻译方式：Demo模式、OpenAI、Claude、Google、DeepL
 */

class Translator {
    constructor() {
        this.service = localStorage.getItem('translation-service') || 'demo';
        this.apiKey = localStorage.getItem('translation-api-key') || '';
        this.cache = new Map();
        this.loadCache();
        this.onProgress = null;
    }

    // 设置翻译服务
    setService(service) {
        this.service = service;
        localStorage.setItem('translation-service', service);
    }

    // 设置API Key
    setApiKey(key) {
        this.apiKey = key;
        localStorage.setItem('translation-api-key', key);
    }

    // 设置进度回调
    setProgressCallback(callback) {
        this.onProgress = callback;
    }

    // 翻译文本
    async translate(text, from = 'zh', to = 'en') {
        if (!text || text.trim().length === 0) return '';

        // 检查缓存
        const cacheKey = `${this.service}:${from}:${to}:${text}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        let result;
        try {
            switch (this.service) {
                case 'openai':
                    result = await this.openaiTranslate(text, from, to);
                    break;
                case 'claude':
                    result = await this.claudeTranslate(text, from, to);
                    break;
                case 'google':
                    result = await this.googleTranslate(text, from, to);
                    break;
                case 'deepl':
                    result = await this.deeplTranslate(text, from, to);
                    break;
                case 'demo':
                default:
                    result = await this.demoTranslate(text, from, to);
            }
        } catch (error) {
            console.error('翻译失败:', error);
            alert(`翻译失败: ${error.message}\n\n请检查:\n1. API Key是否正确\n2. 网络连接\n3. API额度是否充足`);
            throw error;
        }

        // 存入缓存
        this.cache.set(cacheKey, result);
        this.saveCache();
        return result;
    }

    // OpenAI GPT 翻译
    async openaiTranslate(text, from = 'zh', to = 'en') {
        if (!this.apiKey) {
            throw new Error('请先设置 OpenAI API Key');
        }

        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                model: 'gpt-3.5-turbo',
                messages: [
                    {
                        role: 'system',
                        content: 'You are a professional translator. Translate the following Chinese text to English. Keep the original meaning and style. Only return the translation, no explanations.'
                    },
                    {
                        role: 'user',
                        content: text
                    }
                ],
                temperature: 0.3,
                max_tokens: 2000
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'OpenAI API 请求失败');
        }

        const data = await response.json();
        return data.choices[0].message.content.trim();
    }

    // Claude 翻译
    async claudeTranslate(text, from = 'zh', to = 'en') {
        if (!this.apiKey) {
            throw new Error('请先设置 Claude API Key');
        }

        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': this.apiKey,
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: 'claude-3-haiku-20240307',
                max_tokens: 2000,
                messages: [
                    {
                        role: 'user',
                        content: `Translate the following Chinese text to English. Keep the original meaning and style. Only return the translation, no explanations.\n\n${text}`
                    }
                ]
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'Claude API 请求失败');
        }

        const data = await response.json();
        return data.content[0].text.trim();
    }

    // Google Translate API 翻译
    async googleTranslate(text, from = 'zh', to = 'en') {
        if (!this.apiKey) {
            throw new Error('请先设置 Google API Key');
        }

        const url = `https://translation.googleapis.com/language/translate/v2?key=${this.apiKey}`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                q: text,
                source: from,
                target: to,
                format: 'text'
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'Google Translate API 请求失败');
        }

        const data = await response.json();
        return data.data.translations[0].translatedText;
    }

    // DeepL API 翻译
    async deeplTranslate(text, from = 'zh', to = 'en') {
        if (!this.apiKey) {
            throw new Error('请先设置 DeepL API Key');
        }

        // DeepL 使用不同的语言代码
        const langMap = { 'zh': 'ZH', 'en': 'EN-US', 'ja': 'JA', 'ko': 'KO' };
        const targetLang = langMap[to] || 'EN-US';

        const response = await fetch('https://api-free.deepl.com/v2/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `DeepL-Auth-Key ${this.apiKey}`
            },
            body: new URLSearchParams({
                text: text,
                source_lang: from.toUpperCase(),
                target_lang: targetLang
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'DeepL API 请求失败');
        }

        const data = await response.json();
        return data.translations[0].text;
    }

    // Demo模式翻译（模拟AI翻译）
    async demoTranslate(text, from = 'zh', to = 'en') {
        await this.delay(300 + Math.random() * 500);

        const translations = {
            '克劳德': 'Cloud', '蒂法': 'Tifa', '爱丽丝': 'Aerith',
            '巴雷特': 'Barret', '萨菲罗斯': 'Sephiroth', '扎克斯': 'Zack',
            '魔晄': 'Mako', '魔石': 'Materia', '神罗公司': 'Shinra',
            '雪崩': 'AVALANCHE', '生命之流': 'Lifestream', '古代种': 'The Ancients',
            '杰诺瓦': 'Jenova', '米德加': 'Midgar', '星球': 'the Planet',
        };

        let translated = text;
        for (const [cn, en] of Object.entries(translations)) {
            translated = translated.replace(new RegExp(cn, 'g'), en);
        }

        if (translated === text && text.length > 10) {
            translated = this.generateMockTranslation(text);
        } else if (translated === text) {
            translated = `[EN] ${text}`;
        }

        return translated;
    }

    generateMockTranslation(chineseText) {
        const sentences = chineseText.split(/[。！？；]/).filter(s => s.trim());
        return sentences.map(s => this.generateMockWords(Math.max(5, s.length / 2)) + '.').join(' ');
    }

    generateMockWords(count) {
        const words = ['The', 'a', 'in', 'on', 'with', 'from', 'Cloud', 'Tifa', 'Aerith', 'looked', 'felt', 'said'];
        const result = [];
        for (let i = 0; i < count; i++) {
            result.push(words[Math.floor(Math.random() * words.length)];
        }
        let text = result.join(' ').toLowerCase();
        return text.charAt(0).toUpperCase() + text.slice(1);
    }

    // 延迟函数
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // 翻译整章
    async translateChapter(content, onProgress = null) {
        const paragraphs = this.extractParagraphs(content);
        const translatedParagraphs = [];
        
        for (let i = 0; i < paragraphs.length; i++) {
            const para = paragraphs[i];
            if (para.trim()) {
                try {
                    const translated = await this.translate(para);
                    translatedParagraphs.push({
                        original: para,
                        translated: translated,
                        id: `para-${i}`
                    });
                    
                    if (onProgress) {
                        onProgress(i + 1, paragraphs.length);
                    }
                    
                    // 添加小延迟避免API限流
                    if (this.service !== 'demo') {
                        await this.delay(100);
                    }
                } catch (error) {
                    console.error(`翻译段落 ${i} 失败:`, error);
                    translatedParagraphs.push({
                        original: para,
                        translated: `[翻译失败] ${para}`,
                        id: `para-${i}`
                    });
                }
            }
        }
        
        return translatedParagraphs;
    }

    // 翻译多章节
    async translateChapters(chapters, maxChapters = 10, onProgress = null) {
        const results = [];
        const limit = Math.min(chapters.length, maxChapters);
        
        for (let i = 0; i < limit; i++) {
            const chapter = chapters[i];
            
            if (onProgress) {
                onProgress(i + 1, limit, `翻译第 ${i + 1}/${limit} 章...`);
            }
            
            try {
                const translated = await this.translateChapter(chapter.content);
                results.push({
                    title: chapter.title,
                    index: i,
                    paragraphs: translated
                });
            } catch (error) {
                console.error(`翻译章节 ${i} 失败:`, error);
                results.push({
                    title: chapter.title,
                    index: i,
                    paragraphs: [{ translated: '[章节翻译失败]' }]
                });
            }
            
            // 章节之间延迟
            if (this.service !== 'demo') {
                await this.delay(500);
            }
        }
        
        return results;
    }

    extractParagraphs(htmlContent) {
        const temp = document.createElement('div');
        temp.innerHTML = htmlContent;
        
        const paragraphs = [];
        const textElements = temp.querySelectorAll('p, div, h1, h2, h3, h4, h5, h6');
        
        textElements.forEach(el => {
            const text = el.textContent.trim();
            if (text && text.length > 5) {
                paragraphs.push(text);
            }
        });
        
        if (paragraphs.length === 0) {
            const text = temp.textContent || htmlContent;
            return text.split(/[。！？]/).filter(s => s.trim().length > 5);
        }
        
        return paragraphs;
    }

    renderTranslation(translatedParagraphs) {
        const container = document.getElementById('english-content');
        container.innerHTML = translatedParagraphs.map(para => `
            <div class="translation-paragraph" data-para-id="${para.id}">
                ${this.escapeHtml(para.translated)}
            </div>
        `).join('');
    }

    renderMultiChapterTranslation(chapters) {
        const container = document.getElementById('english-content');
        container.innerHTML = chapters.map((chapter, idx) => `
            <div class="chapter-block" data-chapter="${idx}">
                <h3 class="chapter-title">${this.escapeHtml(chapter.title || `第 ${idx + 1} 章`)}</h3>
                ${chapter.paragraphs.map(para => `
                    <div class="translation-paragraph" data-para-id="${para.id}">
                        ${this.escapeHtml(para.translated)}
                    </div>
                `).join('')}
            </div>
        `).join('');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    saveCache() {
        const cacheObj = Object.fromEntries(this.cache);
        localStorage.setItem('translation-cache', JSON.stringify(cacheObj));
    }

    loadCache() {
        try {
            const saved = localStorage.getItem('translation-cache');
            if (saved) {
                const cacheObj = JSON.parse(saved);
                this.cache = new Map(Object.entries(cacheObj));
            }
        } catch (e) {
            console.error('加载缓存失败:', e);
        }
    }

    clearCache() {
        this.cache.clear();
        localStorage.removeItem('translation-cache');
    }
}

// 初始化翻译器
const translator = new Translator();

// 更新加载提示
function updateLoading(show, text = '加载中...') {
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loading-text');
    
    if (show) {
        loading.classList.remove('hidden');
        loadingText.textContent = text;
    } else {
        loading.classList.add('hidden');
    }
}
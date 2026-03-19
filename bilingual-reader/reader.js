/**
 * 双语阅读器核心逻辑
 * 基于 epub.js 构建
 */

// 全局变量
let book = null;
let rendition = null;
let currentChapter = null;
let isBilingualMode = false;
let currentBookType = 'epub'; // 'epub' 或 'txt'
let currentBookData = null; // 存储原始数据

// DOM元素
const els = {
    fileInput: document.getElementById('file-input'),
    btnUpload: document.getElementById('btn-upload'),
    btnToc: document.getElementById('btn-toc'),
    btnPrev: document.getElementById('btn-prev'),
    btnNext: document.getElementById('btn-next'),
    btnMode: document.getElementById('btn-mode'),
    btnTranslate: document.getElementById('btn-translate'),
    btnRetranslate: document.getElementById('btn-retranslate'),
    btnGlossary: document.getElementById('btn-glossary'),
    btnSettings: document.getElementById('btn-settings'),
    chapterSelect: document.getElementById('chapter-select'),
    bookTitle: document.getElementById('book-title'),
    tocPanel: document.getElementById('toc-panel'),
    tocList: document.getElementById('toc-list'),
    viewer: document.getElementById('viewer'),
    chinesePanel: document.getElementById('chinese-panel'),
    englishPanel: document.getElementById('english-panel'),
    englishContent: document.getElementById('english-content'),
    glossaryPanel: document.getElementById('glossary-panel'),
    settingsPanel: document.getElementById('settings-panel'),
    termPopup: document.getElementById('term-popup')
};

// 初始化
function init() {
    bindEvents();
    loadSettings();
    glossaryManager.renderGlossary('characters');
}

// 绑定事件
function bindEvents() {
    // 上传文件
    els.btnUpload.addEventListener('click', () => els.fileInput.click());
    els.fileInput.addEventListener('change', handleFileUpload);

    // 导航按钮
    els.btnToc.addEventListener('click', toggleToc);
    els.btnPrev.addEventListener('click', () => {
        if (currentBookType === 'epub') {
            rendition?.prev();
        } else {
            alert('TXT文件不支持章节导航');
        }
    });
    els.btnNext.addEventListener('click', () => {
        if (currentBookType === 'epub') {
            rendition?.next();
        } else {
            alert('TXT文件不支持章节导航');
        }
    });
    els.chapterSelect.addEventListener('change', handleChapterSelect);

    // 功能按钮
    els.btnMode.addEventListener('click', toggleBilingualMode);
    els.btnTranslate.addEventListener('click', translateCurrentChapter);
    els.btnRetranslate.addEventListener('click', translateCurrentChapter);
    els.btnGlossary.addEventListener('click', toggleGlossary);
    els.btnSettings.addEventListener('click', toggleSettings);

    // 设置面板
    document.getElementById('font-size')?.addEventListener('input', handleFontSizeChange);
    document.getElementById('line-height')?.addEventListener('input', handleLineHeightChange);
    document.getElementById('theme-select')?.addEventListener('change', handleThemeChange);
    document.getElementById('translation-scope')?.addEventListener('change', handleScopeChange);
    document.getElementById('translation-service')?.addEventListener('change', handleServiceChange);
    document.getElementById('api-key')?.addEventListener('input', handleApiKeyChange);

    // 术语表标签切换
    document.querySelectorAll('.glossary-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.glossary-tabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            glossaryManager.renderGlossary(e.target.dataset.tab);
        });
    });

    // 键盘快捷键
    document.addEventListener('keydown', handleKeyboard);

    // 点击外部关闭弹窗
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.term-popup') && !e.target.closest('.term-highlight')) {
            closePopup();
        }
    });
}

// 处理文件上传
function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const fileName = file.name.toLowerCase();
    
    if (fileName.endsWith('.epub')) {
        updateLoading(true, '正在解析书籍...');
        const reader = new FileReader();
        reader.onload = (event) => {
            const arrayBuffer = event.target.result;
            loadBook(arrayBuffer, 'epub', file.name);
        };
        reader.readAsArrayBuffer(file);
    } else if (fileName.endsWith('.txt')) {
        updateLoading(true, '正在加载文本...');
        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target.result;
            loadBook(text, 'txt', file.name);
        };
        reader.readAsText(file, 'UTF-8');
    } else {
        alert('请选择 EPUB 或 TXT 格式的文件');
    }
}

// 加载书籍
function loadBook(data, type, fileName = '') {
    try {
        currentBookType = type;
        currentBookData = data;

        // 如果已有书籍，先清理
        if (book) {
            book.destroy();
            book = null;
        }
        if (rendition) {
            rendition = null;
        }

        if (type === 'txt') {
            loadTxtBook(data, fileName);
        } else {
            loadEpubBook(data);
        }

        updateLoading(false);

    } catch (error) {
        console.error('加载书籍失败:', error);
        alert('加载书籍失败，请检查文件格式');
        updateLoading(false);
    }
}

// 加载 EPUB 书籍
function loadEpubBook(arrayBuffer) {
    // 创建新书
    book = ePub(arrayBuffer);

    book.loaded.metadata.then(metadata => {
        els.bookTitle.textContent = metadata.title || '未知书名';
        document.title = `${metadata.title || '未知书名'} - AI双语阅读器`;
    });

    book.loaded.navigation.then(navigation => {
        renderToc(navigation.toc);
        populateChapterSelect(navigation.toc);
    });

    // 创建渲染
    rendition = book.renderTo(els.viewer, {
        width: '100%',
        height: '100%',
        spread: 'none',
        flow: 'scrolled-doc'
    });

    // 显示第一章
    rendition.display();

    // 监听章节变化
    rendition.on('relocated', (location) => {
        currentChapter = location.start.href;
        updateTocHighlight(location.start.href);
        updateChapterSelect(location.start.href);
        
        // 章节变化时，清空英文面板
        els.englishContent.innerHTML = `
            <div class="placeholder">
                <p>🤖 点击右上角翻译按钮生成英文版本</p>
                <p>Click translate button to generate English version</p>
            </div>
        `;
    });

    // 内容加载后注入术语高亮
    rendition.on('rendered', (section) => {
        highlightTerms(section.document);
    });
}

// 加载 TXT 书籍
function loadTxtBook(text, fileName) {
    els.bookTitle.textContent = fileName.replace('.txt', '') || '文本文件';
    document.title = `${fileName.replace('.txt', '') || '文本文件'} - AI双语阅读器`;
    
    // 清空目录
    els.tocList.innerHTML = '<div class="toc-item">TXT文件无目录</div>';
    els.chapterSelect.innerHTML = '<option>TXT文件无章节</option>';
    
    // 将文本分段（按空行或固定长度）
    const paragraphs = text.split(/\n\s*\n/)
        .filter(p => p.trim().length > 0)
        .map(p => `<p>${p.trim().replace(/\n/g, '<br>')}</p>`);
    
    // 构建简单的HTML
    const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { 
                    font-family: "Noto Serif SC", "Source Han Serif SC", serif;
                    line-height: 1.8; 
                    padding: 40px; 
                    max-width: 700px; 
                    margin: 0 auto;
                    font-size: 16px;
                }
                p { margin-bottom: 1.5em; text-align: justify; }
            </style>
        </head>
        <body>${paragraphs.join('')}</body>
        </html>
    `;
    
    // 清空viewer并创建 iframe
    els.viewer.innerHTML = '';
    const iframe = document.createElement('iframe');
    iframe.id = 'txt-viewer';
    iframe.style.cssText = 'width:100%; height:100%; border:none;';
    els.viewer.appendChild(iframe);
    
    // 写入内容
    iframe.onload = () => {
        highlightTerms(iframe.contentDocument);
    };
    
    const blob = new Blob([htmlContent], { type: 'text/html' });
    iframe.src = URL.createObjectURL(blob);
}

// 渲染目录
function renderToc(toc, level = 0) {
    if (!toc || toc.length === 0) return '';

    let html = level === 0 ? '' : '<ul>';
    
    toc.forEach(item => {
        const indent = level * 20;
        html += `
            <li class="toc-item" style="padding-left: ${indent}px" 
                data-href="${item.href}" 
                onclick="navigateToChapter('${item.href}')">
                ${item.label}
            </li>
        `;
        if (item.subitems) {
            html += renderToc(item.subitems, level + 1);
        }
    });

    html += level === 0 ? '' : '</ul>';
    
    if (level === 0) {
        els.tocList.innerHTML = html;
    }
    return html;
}

// 填充章节选择器
function populateChapterSelect(toc) {
    els.chapterSelect.innerHTML = '';
    
    function addOptions(items, prefix = '') {
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item.href;
            option.textContent = prefix + item.label;
            els.chapterSelect.appendChild(option);
            
            if (item.subitems) {
                addOptions(item.subitems, prefix + '  ');
            }
        });
    }
    
    addOptions(toc);
}

// 更新目录高亮
function updateTocHighlight(href) {
    document.querySelectorAll('.toc-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.href === href) {
            item.classList.add('active');
        }
    });
}

// 更新章节选择器
function updateChapterSelect(href) {
    els.chapterSelect.value = href;
}

// 导航到章节
function navigateToChapter(href) {
    if (rendition) {
        rendition.display(href);
    }
}

// 处理章节选择
function handleChapterSelect(e) {
    const href = e.target.value;
    if (href) {
        navigateToChapter(href);
    }
}

// 切换目录显示
function toggleToc() {
    els.tocPanel.classList.toggle('hidden');
}

// 切换双语模式
function toggleBilingualMode() {
    isBilingualMode = !isBilingualMode;
    document.body.classList.toggle('bilingual-mode', isBilingualMode);
    els.englishPanel.classList.toggle('hidden', !isBilingualMode);
    els.btnMode.title = isBilingualMode ? '切换单语模式' : '切换双语模式';
    
    // 保存设置
    localStorage.setItem('bilingual-mode', isBilingualMode);
}

// 翻译当前章节
async function translateCurrentChapter() {
    // 显示英文面板
    els.englishPanel.classList.remove('hidden');
    document.body.classList.add('bilingual-mode');
    isBilingualMode = true;

    updateLoading(true, '正在翻译...');

    try {
        // 获取翻译范围设置
        const scope = localStorage.getItem('translation-scope') || 'current';
        
        if (currentBookType === 'txt') {
            // TXT文件直接翻译全部内容
            const text = currentBookData;
            const translatedParagraphs = await translator.translateChapter(text, (current, total) => {
                updateLoading(true, `翻译中... ${current}/${total}`);
            });
            translator.renderTranslation(translatedParagraphs);
        } else if (currentBookType === 'epub' && book) {
            // EPUB根据范围翻译
            if (scope === 'current') {
                // 仅翻译当前章节
                await translateCurrentEpubChapter();
            } else {
                // 翻译多个章节
                const maxChapters = scope === 'all' ? Infinity : parseInt(scope);
                await translateMultipleChapters(maxChapters);
            }
        } else {
            alert('请先加载书籍');
            updateLoading(false);
            return;
        }
        
        updateLoading(false);
    } catch (error) {
        console.error('翻译失败:', error);
        alert('翻译失败，请重试');
        updateLoading(false);
    }
}

// 翻译EPUB当前章节
async function translateCurrentEpubChapter() {
    const contents = rendition.getContents();
    if (!contents || contents.length === 0) {
        updateLoading(false);
        return;
    }
    const doc = contents[0].document;
    const text = doc.body.innerText || doc.body.textContent;
    
    const translatedParagraphs = await translator.translateChapter(text, (current, total) => {
        updateLoading(true, `翻译中... ${current}/${total}`);
    });
    
    translator.renderTranslation(translatedParagraphs);
}

// 翻译多个章节
async function translateMultipleChapters(maxChapters) {
    // 获取所有章节
    const spine = book.spine;
    const totalChapters = spine.items.length;
    const chaptersToTranslate = Math.min(totalChapters, maxChapters);
    
    const chapters = [];
    for (let i = 0; i < chaptersToTranslate; i++) {
        const item = spine.items[i];
        const doc = await item.load(book.load.bind(book));
        const content = doc.body.innerText || doc.body.textContent;
        chapters.push({
            title: item.href.split('/').pop() || `第 ${i + 1} 章`,
            content: content
        });
        item.unload();
    }
    
    // 翻译所有章节
    const translatedChapters = await translator.translateChapters(
        chapters, 
        maxChapters,
        (current, total, message) => {
            updateLoading(true, message || `翻译第 ${current}/${total} 章...`);
        }
    );
    
    // 渲染结果
    translator.renderMultiChapterTranslation(translatedChapters);
}

// 术语高亮
function highlightTerms(doc) {
    if (!doc) return;

    // 获取所有术语
    const allTerms = [];
    for (const [type, terms] of Object.entries(glossaryManager.data)) {
        for (const name of Object.keys(terms)) {
            allTerms.push(name);
        }
    }

    // 遍历文本节点并高亮
    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT, null, false);
    const textNodes = [];
    
    while (walker.nextNode()) {
        textNodes.push(walker.currentNode);
    }

    textNodes.forEach(textNode => {
        let text = textNode.textContent;
        let hasMatch = false;

        allTerms.forEach(term => {
            if (text.includes(term)) {
                hasMatch = true;
                text = text.replace(new RegExp(term, 'g'), `<span class="term-highlight" data-term="${term}">${term}</span>`);
            }
        });

        if (hasMatch) {
            const wrapper = doc.createElement('span');
            wrapper.innerHTML = text;
            textNode.parentNode.replaceChild(wrapper, textNode);
        }
    });

    // 绑定术语点击事件
    doc.querySelectorAll('.term-highlight').forEach(el => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            showTermDetail(el.dataset.term);
        });
    });
}

// 显示术语详情
function showTermDetail(termName) {
    const term = glossaryManager.getTerm(termName);
    if (!term) return;

    document.getElementById('term-name').textContent = term.name;
    document.getElementById('term-type').textContent = getTypeLabel(term.type);
    document.getElementById('term-desc').textContent = term.description;
    document.getElementById('term-en').textContent = term.nameEn;

    els.termPopup.classList.remove('hidden');
}

// 关闭弹窗
function closePopup() {
    els.termPopup.classList.add('hidden');
}

// 获取类型标签
function getTypeLabel(type) {
    const labels = {
        character: '人物 Character',
        concept: '概念 Concept',
        place: '地点 Place'
    };
    return labels[type] || type;
}

// 切换术语表面板
function toggleGlossary() {
    els.glossaryPanel.classList.toggle('hidden');
    els.settingsPanel.classList.add('hidden');
}

// 切换设置面板
function toggleSettings() {
    els.settingsPanel.classList.toggle('hidden');
    els.glossaryPanel.classList.add('hidden');
}

// 设置相关
function handleFontSizeChange(e) {
    const size = e.target.value;
    document.getElementById('font-size-value').textContent = size + 'px';
    document.documentElement.style.setProperty('--font-size', size + 'px');
    
    if (rendition) {
        rendition.themes.fontSize(size + 'px');
    }
    
    localStorage.setItem('font-size', size);
}

function handleLineHeightChange(e) {
    const height = e.target.value;
    document.getElementById('line-height-value').textContent = height;
    document.documentElement.style.setProperty('--line-height', height);
    localStorage.setItem('line-height', height);
}

function handleThemeChange(e) {
    const theme = e.target.value;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

function handleScopeChange(e) {
    const scope = e.target.value;
    localStorage.setItem('translation-scope', scope);
}

function handleServiceChange(e) {
    const service = e.target.value;
    translator.setService(service);
    
    // 显示/隐藏API Key输入框
    const apiKeyContainer = document.getElementById('api-key-container');
    if (apiKeyContainer) {
        apiKeyContainer.style.display = service === 'demo' ? 'none' : 'block';
    }
}

function handleApiKeyChange(e) {
    const key = e.target.value;
    translator.setApiKey(key);
}

function loadSettings() {
    // 字体大小
    const fontSize = localStorage.getItem('font-size') || '16';
    document.getElementById('font-size').value = fontSize;
    document.getElementById('font-size-value').textContent = fontSize + 'px';
    
    // 行高
    const lineHeight = localStorage.getItem('line-height') || '1.6';
    document.getElementById('line-height').value = lineHeight;
    document.getElementById('line-height-value').textContent = lineHeight;
    
    // 主题
    const theme = localStorage.getItem('theme') || 'light';
    document.getElementById('theme-select').value = theme;
    document.documentElement.setAttribute('data-theme', theme);
    
    // 双语模式
    const bilingual = localStorage.getItem('bilingual-mode') === 'true';
    if (bilingual) {
        toggleBilingualMode();
    }
    
    // 翻译范围
    const scope = localStorage.getItem('translation-scope') || 'current';
    const scopeSelect = document.getElementById('translation-scope');
    if (scopeSelect) {
        scopeSelect.value = scope;
    }
    
    // 翻译服务
    const service = localStorage.getItem('translation-service') || 'demo';
    const serviceSelect = document.getElementById('translation-service');
    if (serviceSelect) {
        serviceSelect.value = service;
    }
    
    // API Key
    const apiKey = localStorage.getItem('translation-api-key') || '';
    const apiKeyInput = document.getElementById('api-key');
    if (apiKeyInput) {
        apiKeyInput.value = apiKey;
    }
    
    // 控制API Key输入框显示
    const apiKeyContainer = document.getElementById('api-key-container');
    if (apiKeyContainer) {
        apiKeyContainer.style.display = service === 'demo' ? 'none' : 'block';
    }
}

// 键盘快捷键
function handleKeyboard(e) {
    // 忽略输入框
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    switch (e.key) {
        case 'ArrowLeft':
            if (currentBookType === 'epub') {
                rendition?.prev();
            }
            break;
        case 'ArrowRight':
        case ' ':
            if (currentBookType === 'epub') {
                rendition?.next();
            }
            break;
        case 'b':
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                toggleBilingualMode();
            }
            break;
        case 't':
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                translateCurrentChapter();
            }
            break;
        case 'g':
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                toggleGlossary();
            }
            break;
        case 'Escape':
            closePopup();
            els.glossaryPanel.classList.add('hidden');
            els.settingsPanel.classList.add('hidden');
            break;
    }
}

// 更新加载状态
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

// 启动
window.addEventListener('DOMContentLoaded', init);
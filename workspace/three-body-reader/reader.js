/**
 * 三体交互阅读器 - 核心逻辑
 * Three-Body Problem Interactive Reader
 */

// ===== 全局状态 =====
const state = {
    pdfDoc: null,
    currentPage: 1,
    totalPages: 0,
    scale: 1.5,
    fileName: ''
};

// ===== 角色数据 =====
const characters = {
    wangmiao: {
        name: '汪淼',
        role: '纳米材料科学家',
        avatar: '#4A90D9',
        description: `汪淼是《三体》第一部的主角之一，一位研究纳米材料的科学家。

他在调查科学家自杀事件的过程中，逐渐发现了"科学边界"组织和三体世界的存在。

<b>关键事件：</b>
• 发现"宇宙闪烁"现象
• 进入三体游戏，了解三体文明
• 参与古筝行动，摧毁审判日号

<b>性格特点：</b>理性、坚韧，面对超自然现象时保持了科学家的冷静。`,
        firstAppearance: '第一章：科学边界',
        books: ['第一部：地球往事']
    },
    yewenjie: {
        name: '叶文洁',
        role: '天体物理学家',
        avatar: '#E74C3C',
        description: `叶文洁是《三体》系列中最关键的人物之一，红岸基地的天体物理学家。

<b>核心行动：</b>
• 在文革期间被派往红岸基地
• 发现了太阳能量镜面增益效应
• 向宇宙发出了地球的第一声啼鸣
• 成为地球三体组织（ETO）的精神领袖

<b>复杂性：</b>
她既是人类文明的"叛徒"，又是一位对人类失望的理想主义者。她的经历反映了那个特殊时代对人性的摧残。`,
        firstAppearance: '第五章：叶文洁',
        books: ['第一部：地球往事', '第二部：黑暗森林（回忆）']
    },
    shiqiang: {
        name: '史强',
        role: '刑警',
        avatar: '#27AE60',
        description: `史强（大史）是警方派来保护科学家的刑警，外表粗犷但内心细腻。

<b>重要作用：</b>
• 保护汪淼等科学家
• 提出古筝行动的创意
• 用 pragmatic 的方式对抗三体威胁

<b>名言：</b>
"虫子从来没有被真正战胜过。"

<b>性格特点：</b>
看似粗鲁但极具洞察力，善于用简单直接的方式解决复杂问题。他是连接科学家和普通人的桥梁。`,
        firstAppearance: '第一章：科学边界',
        books: ['第一部：地球往事', '第二部：黑暗森林']
    },
    luoji: {
        name: '罗辑',
        role: '面壁者、执剑人',
        avatar: '#9B59B6',
        description: `罗辑是《三体》第二部《黑暗森林》的主角，一位原本玩世不恭的社会学教授。

<b>蜕变之路：</b>
• 被选为面壁者之一
• 领悟"黑暗森林"法则
• 建立对三体世界的威慑
• 成为第一代执剑人

<b>黑暗森林法则：</b>
宇宙就是一座黑暗森林，每个文明都是带枪的猎人...

<b>牺牲：</b>
为了维持威慑，他付出了与家人分离的代价，独自在地下掩体中度过了数十年。`,
        firstAppearance: '第二部：面壁者',
        books: ['第二部：黑暗森林', '第三部：死神永生（回忆）']
    },
    chengxin: {
        name: '程心',
        role: '执剑人、星环公司CEO',
        avatar: '#F39C12',
        description: `程心是《三体》第三部《死神永生》的主角，代表着人类的爱与仁慈。

<b>关键抉择：</b>
• 成为第二代执剑人
• 在威慑博弈中放弃威慑
• 提出阶梯计划
• 参与光速飞船研发

<b>争议性：</b>
她被读者称为"圣母"，因为她的仁慈导致了地球的毁灭。但她的选择也反映了人性的复杂——在极端环境下，善良是否还是一种美德？

<b>最终：</b>
她见证了宇宙的重生，成为了人类文明的最后记录者。`,
        firstAppearance: '第三部：魔法师之死',
        books: ['第三部：死神永生']
    }
};

// ===== 概念数据 =====
const concepts = {
    sophon: {
        name: '智子（Sophon）',
        quote: '我们封锁了你们的科学。',
        description: `智子是三体文明制造的高维智能粒子，通过二维展开和电路蚀刻技术，将单个质子改造成超级计算机。

<b>功能：</b>
• 干扰地球粒子对撞实验，封锁基础物理学发展
• 在地球和舰队间进行即时通信
• 可以拟态成任何形态，监视人类社会

<b>象征意义：</b>
智子代表了科技代差——当一种文明能够操控物质的基本结构时，另一种文明连理解这种能力都做不到。`,
        related: ['三体文明', '科学封锁', '高维空间']
    },
    darkforest: {
        name: '黑暗森林法则',
        quote: '宇宙就是一座黑暗森林，每个文明都是带枪的猎人。',
        description: `罗辑领悟的宇宙社会学基本法则，解释了费米悖论——为什么宇宙如此安静。

<b>基本公理：</b>
1. 生存是文明的第一需要
2. 文明不断增长和扩张，但宇宙中的物质总量保持不变

<b>猜疑链：</b>
文明之间无法判断对方是善意还是恶意

<b>技术爆炸：</b>
弱小的文明可能突然获得超越强者的技术

<b>结论：</b>
发现即毁灭。任何暴露自己位置的文明都会被消灭。这就是宇宙的"黑暗森林"状态。`,
        related: ['罗辑', '宇宙社会学', '费米悖论']
    },
    droplet: {
        name: '水滴（强互作用力探测器）',
        quote: '它的表面是绝对光滑的。',
        description: `三体文明发射的探测器，形状像一滴水银，却拥有毁灭性的力量。

<b>技术特点：</b>
• 表面由强互作用力材料构成，绝对光滑
• 温度接近绝对零度
• 硬度超过地球任何材料
• 能够锐角转向，违反动量守恒

<b>战绩：</b>
仅凭一颗水滴，就摧毁了人类的太空舰队——2000艘战舰在几分钟内被全灭。

<b>象征：</b>
水滴展示了"技术代差"的残酷——人类以为是决战，对方只是派来一个探测器。`,
        related: ['三体舰队', '末日战役', '强互作用力材料']
    },
    dimensional: {
        name: '降维打击',
        quote: '我需要一块二向箔，清理用。',
        description: `高级文明使用的清理工具，将三维空间压缩成二维。

<b>原理：</b>
通过二向箔展开，将三维空间的一维"展开"到二维，导致三维结构坍塌。

<b>结果：</b>
整个太阳系被二维化，变成了一幅没有厚度的画。

<b>逃逸方法：</b>
只有达到光速才能逃脱——这就是"星环号"研发光速飞船的意义。

<b>哲学意味：</b>
降维打击是宇宙中最残酷的攻击方式，它不针对某个文明，而是整个空间结构。`,
        related: ['二向箔', '歌者文明', '掩体计划', '星环号']
    },
    sword: {
        name: '执剑人',
        quote: '他握着两个世界的命运。',
        description: `掌握对三体世界威慑力量的人，可以随时暴露三体星系的位置，引来黑暗森林打击。

<b>威慑原理：</b>
• 如果三体舰队入侵，执剑人将广播三体坐标
• 这会导致三体世界被毁灭
• 但地球坐标也会因此暴露
• 最终结果是双输

<b>两任执剑人：</b>
• 罗辑（威慑维持者，威慑度90%）
• 程心（爱与仁慈，威慑度10%）

<b>悲剧：</b>
人类选择了程心，因为罗辑太冷酷。但正是这个选择导致了威慑失败。`,
        related: ['罗辑', '程心', '黑暗森林威慑', '引力波广播']
    },
    wall: {
        name: '面壁者',
        quote: '这是计划的一部分。',
        description: `联合国选出的四位战略家，他们可以利用全球资源实施对抗三体的计划，而不需要向任何人解释。

<b>面壁者名单：</b>
• 弗里德里克·泰勒（前美国国防部长）
• 曼努尔·雷迪亚兹（前委内瑞拉总统）
• 比尔·希恩斯（英国脑科学家）
• 罗辑（中国社会学家）

<b>破壁人：</b>
地球三体组织派出的对应者，专门破解面壁计划。

<b>最终：</b>
只有罗辑的计划成功了——不是因为他最聪明，而是因为他悟出了宇宙的真相。`,
        related: ['罗辑', '破壁人', '地球三体组织', '行星防御理事会']
    },
    eto: {
        name: '地球三体组织（ETO）',
        quote: '消灭人类暴政，世界属于三体！',
        description: `人类中的叛徒组织，认为三体文明能够拯救腐败的人类社会。

<b>三个派别：</b>
• <b>降临派：</b>想让三体人毁灭人类，对人类绝望
• <b>拯救派：</b>想解决三体问题，让两个文明共存
• <b>幸存派：</b>想在三体统治下苟活，出卖同胞换取生存

<b>核心矛盾：</b>
ETO成员并非都是坏人，很多人是出于对人类社会的失望。但他们的选择最终证明是错误的——三体人从未想过与人类共存。

<b>结局：</b>
古筝行动摧毁了ETO的总部，但组织的影响一直延续。`,
        related: ['叶文洁', '伊文斯', '审判日号', '古筝行动']
    },
    red: {
        name: '红岸基地',
        quote: '不要回答！不要回答！！不要回答！！！',
        description: `中国1960年代建立的射电天文观测基地，表面上是研究太阳活动，实际任务是寻找地外文明。

<b>核心设施：</b>
巨大的抛物面天线，可以向宇宙发送大功率无线电信号。

<b>历史意义：</b>
• 叶文洁在这里向三体世界发送了信号
• 收到了"不要回答"的警告
• 但她还是回答了，开启了人类的灾难

<b>象征：</b>
红岸基地是人类好奇心的产物——既可能带来知识的飞跃，也可能招来灭顶之灾。`,
        related: ['叶文洁', '射电望远镜', '太阳放大器', '不要回答']
    }
};

// ===== PDF.js 配置 =====
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// ===== DOM 元素 =====
const elements = {
    fileInput: document.getElementById('pdf-upload'),
    canvas: document.getElementById('pdf-canvas'),
    emptyState: document.getElementById('empty-state'),
    pageInput: document.getElementById('page-input'),
    totalPages: document.getElementById('total-pages'),
    prevPage: document.getElementById('prev-page'),
    nextPage: document.getElementById('next-page'),
    zoomIn: document.getElementById('zoom-in'),
    zoomOut: document.getElementById('zoom-out'),
    zoomLevel: document.getElementById('zoom-level'),
    charModal: document.getElementById('char-modal'),
    conceptModal: document.getElementById('concept-modal')
};

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    initCharacterInteractions();
    initConceptInteractions();
    initChapterInteractions();
});

function initEventListeners() {
    // 文件上传
    elements.fileInput.addEventListener('change', handleFileUpload);
    
    // 拖拽上传
    document.addEventListener('dragover', (e) => e.preventDefault());
    document.addEventListener('drop', handleDrop);
    
    // 页面导航
    elements.prevPage.addEventListener('click', () => changePage(-1));
    elements.nextPage.addEventListener('click', () => changePage(1));
    elements.pageInput.addEventListener('change', (e) => goToPage(parseInt(e.target.value)));
    
    // 缩放控制
    elements.zoomIn.addEventListener('click', () => changeZoom(0.2));
    elements.zoomOut.addEventListener('click', () => changeZoom(-0.2));
    
    // 键盘快捷键
    document.addEventListener('keydown', handleKeydown);
}

// ===== 文件处理 =====
function handleFileUpload(e) {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
        loadPDF(file);
    }
}

function handleDrop(e) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
        loadPDF(file);
    }
}

async function loadPDF(file) {
    try {
        state.fileName = file.name;
        const arrayBuffer = await file.arrayBuffer();
        state.pdfDoc = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        state.totalPages = state.pdfDoc.numPages;
        state.currentPage = 1;
        
        elements.totalPages.textContent = state.totalPages;
        elements.emptyState.style.display = 'none';
        elements.canvas.classList.add('loaded');
        
        renderPage(state.currentPage);
    } catch (error) {
        console.error('Error loading PDF:', error);
        alert('无法加载PDF文件，请检查文件是否损坏。');
    }
}

// ===== 页面渲染 =====
async function renderPage(pageNum) {
    if (!state.pdfDoc) return;
    
    try {
        const page = await state.pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale: state.scale });
        
        elements.canvas.width = viewport.width;
        elements.canvas.height = viewport.height;
        
        const ctx = elements.canvas.getContext('2d');
        ctx.clearRect(0, 0, elements.canvas.width, elements.canvas.height);
        
        await page.render({
            canvasContext: ctx,
            viewport: viewport
        }).promise;
        
        state.currentPage = pageNum;
        elements.pageInput.value = pageNum;
        
        updateChapterHighlight(pageNum);
    } catch (error) {
        console.error('Error rendering page:', error);
    }
}

function changePage(delta) {
    const newPage = state.currentPage + delta;
    if (newPage >= 1 && newPage <= state.totalPages) {
        renderPage(newPage);
    }
}

function goToPage(pageNum) {
    if (pageNum >= 1 && pageNum <= state.totalPages) {
        renderPage(pageNum);
    } else {
        elements.pageInput.value = state.currentPage;
    }
}

function changeZoom(delta) {
    state.scale = Math.max(0.5, Math.min(3, state.scale + delta));
    elements.zoomLevel.textContent = Math.round(state.scale * 100) + '%';
    renderPage(state.currentPage);
}

function handleKeydown(e) {
    if (!state.pdfDoc) return;
    
    switch(e.key) {
        case 'ArrowLeft':
        case 'PageUp':
            changePage(-1);
            break;
        case 'ArrowRight':
        case 'PageDown':
        case ' ':
            changePage(1);
            break;
        case 'Home':
            goToPage(1);
            break;
        case 'End':
            goToPage(state.totalPages);
            break;
    }
}

// ===== 章节导航 =====
function initChapterInteractions() {
    document.querySelectorAll('.chapter-item').forEach(item => {
        item.addEventListener('click', () => {
            const page = parseInt(item.dataset.page);
            if (state.pdfDoc) {
                goToPage(page);
            } else {
                alert('请先上传PDF文件');
            }
        });
    });
}

function togglePart(partId) {
    const part = document.getElementById(partId);
    const toggle = document.querySelector(`[onclick="togglePart('${partId}')"] .toggle-icon`);
    
    if (part.classList.contains('collapsed')) {
        part.classList.remove('collapsed');
        toggle.classList.remove('collapsed');
    } else {
        part.classList.add('collapsed');
        toggle.classList.add('collapsed');
    }
}

function updateChapterHighlight(currentPage) {
    document.querySelectorAll('.chapter-item').forEach(item => {
        item.classList.remove('active');
        const page = parseInt(item.dataset.page);
        // 简化逻辑：高亮当前章节
        if (currentPage >= page) {
            item.classList.add('active');
        }
    });
}

// ===== 角色交互 =====
function initCharacterInteractions() {
    document.querySelectorAll('.char-item').forEach(item => {
        item.addEventListener('click', () => {
            const charId = item.dataset.char;
            showCharacterDetail(charId);
        });
    });
}

function showCharacterDetail(charId) {
    const char = characters[charId];
    if (!char) return;
    
    const modalBody = document.getElementById('char-modal-body');
    document.getElementById('char-modal-title').textContent = '角色详情';
    
    modalBody.innerHTML = `
        <div class="char-detail">
            <div class="char-detail-avatar" style="background: ${char.avatar}">
                ${char.name[0]}
            </div>
            <div class="char-detail-name">${char.name}</div>
            <div class="char-detail-role">${char.role}</div>
            <div class="char-detail-desc">
                ${char.description.replace(/\n/g, '<br>')}
            </div>
        </div>
    `;
    
    elements.charModal.classList.add('active');
}

function closeModal() {
    elements.charModal.classList.remove('active');
}

// ===== 概念交互 =====
function initConceptInteractions() {
    document.querySelectorAll('.concept-tag').forEach(tag => {
        tag.addEventListener('click', () => {
            const conceptId = tag.dataset.concept;
            showConceptDetail(conceptId);
        });
    });
}

function showConceptDetail(conceptId) {
    const concept = concepts[conceptId];
    if (!concept) return;
    
    const modalBody = document.getElementById('concept-modal-body');
    document.getElementById('concept-modal-title').textContent = '概念详解';
    
    modalBody.innerHTML = `
        <div class="concept-detail">
            <h4>${concept.name}</h4>
            <div class="concept-quote">"${concept.quote}"</div>
            <p>${concept.description.replace(/\n/g, '<br>')}</p>
        </div>
    `;
    
    elements.conceptModal.classList.add('active');
}

function closeConceptModal() {
    elements.conceptModal.classList.remove('active');
}

// ===== 点击模态框外部关闭 =====
elements.charModal.addEventListener('click', (e) => {
    if (e.target === elements.charModal) {
        closeModal();
    }
});

elements.conceptModal.addEventListener('click', (e) => {
    if (e.target === elements.conceptModal) {
        closeConceptModal();
    }
});

// ===== 时间线交互 =====
document.querySelectorAll('.timeline-item').forEach(item => {
    item.addEventListener('click', () => {
        const era = item.dataset.era;
        // 可以扩展：显示该时代的详细信息
        console.log('Selected era:', era);
    });
});

// ===== 导出函数到全局（供HTML调用） =====
window.togglePart = togglePart;
window.closeModal = closeModal;
window.closeConceptModal = closeConceptModal;

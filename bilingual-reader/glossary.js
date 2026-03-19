/**
 * 术语表数据 - 示例数据
 * 用户可以通过界面添加自己的术语，或导入JSON文件
 */
const GLOSSARY_DATA = {
    // 人物
    characters: {
        "克劳德": {
            name: "克劳德",
            nameEn: "Cloud",
            type: "character",
            description: "曾是神罗公司的精英战士（Soldier 1st Class），现以雇佣兵身份生活。拥有神秘过去的剑士，使用巨大的破坏剑作为武器。",
            tags: ["主角", "神罗", "Soldier"]
        },
        "蒂法": {
            name: "蒂法",
            nameEn: "Tifa Lockhart",
            type: "character",
            description: "克劳德的青梅竹马，第七天堂酒吧的店主。擅长格斗技，是反神罗组织雪崩的核心成员。",
            tags: ["雪崩", "格斗家", "第七天堂"]
        },
        "爱丽丝": {
            name: "爱丽丝",
            nameEn: "Aerith Gainsborough",
            type: "character",
            description: "古代种塞特拉（Cetra）的最后传人，能够在星球上听到生命之流的声音。在第五区贫民窟卖花。",
            tags: ["古代种", "塞特拉", "卖花女"]
        },
        "巴雷特": {
            name: "巴雷特",
            nameEn: "Barret Wallace",
            type: "character",
            description: "雪崩组织的领袖，为了星球而战的前矿工。右手改装为机关枪，性格激烈但深爱养女玛琳。",
            tags: ["雪崩领袖", "矿工", "玛琳的父亲"]
        },
        "萨菲罗斯": {
            name: "萨菲罗斯",
            nameEn: "Sephiroth",
            type: "character",
            description: "传说中的英雄，神罗公司最强的Soldier 1st Class。后发现自己是外星生命体杰诺瓦的产物，走向疯狂。",
            tags: ["反派", "传奇英雄", "杰诺瓦"]
        },
        "扎克斯": {
            name: "扎克斯",
            nameEn: "Zack Fair",
            type: "character",
            description: "克劳德在神罗时的前辈和朋友，Soldier 1st Class。为了保护克劳德而牺牲，其记忆和人格深刻影响了克劳德。",
            tags: ["Soldier", "前辈", "已牺牲"]
        }
    },

    // 概念
    concepts: {
        "魔晄": {
            name: "魔晄",
            nameEn: "Mako",
            type: "concept",
            description: "星球的血液和生命力。神罗公司抽取魔晄作为能源使用，导致星球逐渐枯萎。过度接触魔晄会导致魔晄中毒。",
            tags: ["能源", "星球", "神罗"]
        },
        "魔石": {
            name: "魔石",
            nameEn: "Materia",
            type: "concept",
            description: "由凝固的魔晄形成的魔法石，可以嵌入装备中使用魔法、召唤兽或增强能力。分为魔法魔石、召唤魔石、支援魔石等类型。",
            tags: ["魔法", "装备", "魔晄"]
        },
        "神罗公司": {
            name: "神罗公司",
            nameEn: "Shinra Electric Power Company",
            type: "concept",
            description: "统治世界的巨大企业垄断集团，通过控制魔晄能源支配全球经济和政治。拥有自己的军队和特种战士组织Soldier。",
            tags: ["企业", "能源", "统治"]
        },
        "雪崩": {
            name: "雪崩",
            nameEn: "AVALANCHE",
            type: "concept",
            description: "反抗神罗公司的生态恐怖组织，主张停止使用魔晄以保护星球。主要基地在第七区贫民窟。",
            tags: ["反抗组织", "生态", "反神罗"]
        },
        "生命之流": {
            name: "生命之流",
            nameEn: "Lifestream",
            type: "concept",
            description: "星球生命力的流动，所有生命死亡后回归的能量的集合。古代种塞特拉能够与生命之流沟通。",
            tags: ["星球", "生命", "能量"]
        },
        "古代种": {
            name: "古代种",
            nameEn: "The Ancients / Cetra",
            type: "concept",
            description: "传说中能够与星球对话的古代民族，能够听到生命之流的声音并找到应许之地。爱丽丝是已知的最后传人。",
            tags: ["古代民族", "塞特拉", "应许之地"]
        },
        "杰诺瓦": {
            name: "杰诺瓦",
            nameEn: "Jenova",
            type: "concept",
            description: "约2000年前从天而降的外星生命体，拥有极强的感染和模仿能力。被认为是赛特拉灭绝的元凶。萨菲罗斯被植入其细胞。",
            tags: ["外星生命", "感染", "灾难"]
        },
        "Soldier": {
            name: "Soldier",
            nameEn: "SOLDIER",
            type: "concept",
            description: "神罗公司的精英战士部队，通过魔晄浸泡和杰诺瓦细胞植入获得超越常人的能力。分为1st、2nd、3rd三个等级。",
            tags: ["战士", "神罗军队", "精英"]
        }
    },

    // 地点
    places: {
        "米德加": {
            name: "米德加",
            nameEn: "Midgar",
            type: "place",
            description: "神罗公司建造的巨大圆形城市，由上下两部分组成。上层是神罗总部和富裕区，下层是八个贫民窟（Sector 0-8）。",
            tags: ["城市", "神罗", "首都"]
        },
        "第七区贫民窟": {
            name: "第七区贫民窟",
            nameEn: "Sector 7 Slums",
            type: "place",
            description: "米德加下层的贫民窟之一，蒂法的第七天堂酒吧所在地。雪崩组织在此设有秘密基地。",
            tags: ["贫民窟", "第七天堂", "雪崩基地"]
        },
        "第五区贫民窟": {
            name: "第五区贫民窟",
            nameEn: "Sector 5 Slums",
            type: "place",
            description: "米德加下层的贫民窟之一，爱丽丝居住的教堂和家所在的地方。",
            tags: ["贫民窟", "教堂", "爱丽丝的家"]
        },
        "神罗大厦": {
            name: "神罗大厦",
            nameEn: "Shinra Building",
            type: "place",
            description: "位于米德加上层的神罗公司总部，高达70层。顶层是总裁办公室，下层包括科研部门、士兵训练设施等。",
            tags: ["神罗总部", "企业", "米德加上层"]
        },
        "星陨峡谷": {
            name: "星陨峡谷",
            nameEn: "Cosmo Canyon",
            type: "place",
            description: "位于悬崖上的学术研究村落，是研究星球和生命之流的圣地。赤红十三的故乡。",
            tags: ["研究", "圣地", "赤红十三"]
        }
    }
};

/**
 * 术语管理器
 */
class GlossaryManager {
    constructor() {
        this.data = { ...GLOSSARY_DATA };
        this.currentTab = 'characters';
    }

    // 获取所有术语（按类型）
    getTermsByType(type) {
        return this.data[type] || {};
    }

    // 搜索术语
    searchTerm(query) {
        const results = [];
        for (const [type, terms] of Object.entries(this.data)) {
            for (const [name, info] of Object.entries(terms)) {
                if (name.includes(query) || 
                    info.nameEn.toLowerCase().includes(query.toLowerCase()) ||
                    info.description.includes(query)) {
                    results.push({ name, ...info });
                }
            }
        }
        return results;
    }

    // 获取单个术语
    getTerm(name) {
        for (const [type, terms] of Object.entries(this.data)) {
            if (terms[name]) {
                return { name, ...terms[name] };
            }
        }
        return null;
    }

    // 添加术语
    addTerm(name, info) {
        const type = info.type || 'concepts';
        if (!this.data[type]) {
            this.data[type] = {};
        }
        this.data[type][name] = info;
        this.saveToStorage();
    }

    // 保存到本地存储
    saveToStorage() {
        localStorage.setItem('bilingual-reader-glossary', JSON.stringify(this.data));
    }

    // 从本地存储加载
    loadFromStorage() {
        const saved = localStorage.getItem('bilingual-reader-glossary');
        if (saved) {
            this.data = { ...this.data, ...JSON.parse(saved) };
        }
    }

    // 导出为JSON
    exportToJSON() {
        return JSON.stringify(this.data, null, 2);
    }

    // 从JSON导入
    importFromJSON(json) {
        try {
            const data = JSON.parse(json);
            this.data = { ...this.data, ...data };
            this.saveToStorage();
            return true;
        } catch (e) {
            console.error('导入失败:', e);
            return false;
        }
    }

    // 渲染术语列表
    renderGlossary(type) {
        const container = document.getElementById('glossary-content');
        const terms = this.getTermsByType(type);

        container.innerHTML = Object.entries(terms).map(([name, info]) => `
            <div class="glossary-item" data-name="${name}" onclick="showTermDetail('${name}')">
                <div class="item-name">${name}</div>
                <div class="item-type">${info.nameEn}</div>
            </div>
        `).join('');
    }
}

// 初始化术语管理器
const glossaryManager = new GlossaryManager();
glossaryManager.loadFromStorage();
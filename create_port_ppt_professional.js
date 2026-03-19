const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = "港口物流服务供应链";

// 专业商务配色 - 港口物流主题
const theme = {
    primary: "1E3A5F",      // 深海蓝 - 主色
    secondary: "2D4A6F",    // 次深蓝
    accent: "D97706",       // 琥珀金 - 点缀
    warmGray: "6B7280",     // 暖灰 - 辅助
    lightGray: "F3F4F6",    // 浅灰背景
    white: "FFFFFF",
    textDark: "1F2937",     // 深色文字
    textLight: "9CA3AF",    // 浅色文字
    border: "E5E7EB"        // 边框色
};

// ===== 第1页：封面 =====
let slide = pres.addSlide();

// 顶部深海蓝横幅
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 2.5,
    fill: { color: theme.primary }
});

// 装饰线
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 2.5, w: 10, h: 0.05,
    fill: { color: theme.accent }
});

// 主标题
slide.addText("港口物流服务供应链", {
    x: 0, y: 0.8, w: 10, h: 0.8,
    fontSize: 40, bold: true,
    color: theme.white, align: "center", fontFace: "Microsoft YaHei"
});

// 副标题
slide.addText("Port Logistics Service Supply Chain", {
    x: 0, y: 1.6, w: 10, h: 0.5,
    fontSize: 14,
    color: "93C5FD", align: "center", fontFace: "Calibri"
});

// 底部信息区
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 2.55, w: 10, h: 3.075,
    fill: { color: theme.lightGray }
});

// 三个信息卡片
const cards = [
    { title: "上游供应商", desc: "物流配给\n配套服务", x: 1 },
    { title: "核心服务", desc: "港口物流\n全流程", x: 4 },
    { title: "下游客户", desc: "销售商\n终端需求", x: 7 }
];

cards.forEach(card => {
    // 卡片背景
    slide.addShape(pres.shapes.RECTANGLE, {
        x: card.x, y: 3.2, w: 2, h: 1.8,
        fill: { color: theme.white },
        line: { color: theme.border, width: 1 }
    });
    
    // 顶部色条
    slide.addShape(pres.shapes.RECTANGLE, {
        x: card.x, y: 3.2, w: 2, h: 0.08,
        fill: { color: theme.accent }
    });
    
    // 标题
    slide.addText(card.title, {
        x: card.x, y: 3.4, w: 2, h: 0.4,
        fontSize: 14, bold: true,
        color: theme.primary, align: "center", fontFace: "Microsoft YaHei"
    });
    
    // 描述
    slide.addText(card.desc, {
        x: card.x, y: 3.9, w: 2, h: 0.8,
        fontSize: 11,
        color: theme.warmGray, align: "center", fontFace: "Microsoft YaHei"
    });
});

// 连接箭头
slide.addText("→", { x: 3, y: 3.8, w: 1, h: 0.5, fontSize: 24, color: theme.accent, align: "center" });
slide.addText("→", { x: 6, y: 3.8, w: 1, h: 0.5, fontSize: 24, color: theme.accent, align: "center" });

// ===== 第2页：供应链全景图 =====
slide = pres.addSlide();
slide.background = { color: theme.lightGray };

// 标题栏
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.7,
    fill: { color: theme.primary }
});
slide.addText("供应链全景图", {
    x: 0.5, y: 0.15, w: 9, h: 0.4,
    fontSize: 18, bold: true,
    color: theme.white, align: "left", fontFace: "Microsoft YaHei"
});

// === 顶部：物流配给供应商 ===
const topY = 0.9;
slide.addShape(pres.shapes.RECTANGLE, {
    x: 3, y: topY, w: 4, h: 0.6,
    fill: { color: theme.white },
    line: { color: theme.primary, width: 2 }
});
slide.addShape(pres.shapes.RECTANGLE, {
    x: 3, y: topY, w: 4, h: 0.08,
    fill: { color: theme.primary }
});
slide.addText("物流配给供应商", {
    x: 3, y: topY + 0.15, w: 4, h: 0.3,
    fontSize: 12, bold: true,
    color: theme.primary, align: "center", fontFace: "Microsoft YaHei"
});

// 5个子项
const supItems = ["港务工程", "修造船厂", "燃料公司", "水电公司", "其他配套"];
const supW = 0.7;
const supGap = 0.08;
const supStartX = 3.1;
supItems.forEach((item, i) => {
    const x = supStartX + i * (supW + supGap);
    slide.addShape(pres.shapes.RECTANGLE, {
        x: x, y: topY + 0.9, w: supW, h: 0.22,
        fill: { color: theme.secondary }
    });
    slide.addText(item, {
        x: x, y: topY + 0.9, w: supW, h: 0.22,
        fontSize: 7, bold: true,
        color: theme.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 向下箭头
slide.addShape(pres.shapes.LINE, {
    x: 4.9, y: 1.52, w: 0, h: 0.18,
    line: { color: theme.accent, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});
slide.addShape(pres.shapes.LINE, {
    x: 5.1, y: 1.52, w: 0, h: 0.18,
    line: { color: theme.accent, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});

// === 中间主体 ===
const mainY = 1.75;
const mainH = 2.4;
const mainX = 1.5;
const mainW = 6.2;

// 供应商椭圆
slide.addShape(pres.shapes.OVAL, {
    x: 0.3, y: mainY + 0.6, w: 0.85, h: 1.1,
    fill: { color: theme.white },
    line: { color: theme.accent, width: 2.5 }
});
slide.addText("供应商", {
    x: 0.3, y: mainY + 0.6, w: 0.85, h: 1.1,
    fontSize: 12, bold: true,
    color: theme.accent, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 1.2, y: mainY + 1.05, w: 0.2, h: 0,
    line: { color: theme.warmGray, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
});
slide.addShape(pres.shapes.LINE, {
    x: 1.2, y: mainY + 1.25, w: 0.2, h: 0,
    line: { color: theme.warmGray, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 5 }
});

// 港口物流主框
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX, y: mainY, w: mainW, h: mainH,
    fill: { color: theme.white },
    line: { color: theme.primary, width: 2 }
});

// 竖向标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX + 0.1, y: mainY + 0.4, w: 0.38, h: 1.6,
    fill: { color: theme.primary }
});
slide.addText("港\n口\n物\n流\n服\n务\n商", {
    x: mainX + 0.1, y: mainY + 0.4, w: 0.38, h: 1.6,
    fontSize: 10, bold: true,
    color: theme.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 左侧7项服务
const svcX = mainX + 0.55;
const svcW = 2.4;
const svcH = 0.26;
const rowH = 0.32;

const services = [
    { name: "引航服务：拖轮公司", arrow: false },
    { name: "理货服务：理货公司", arrow: false },
    { name: "配送服务提供商", arrow: true },
    { name: "运输服务提供商", arrow: true },
    { name: "装卸服务：装卸公司", arrow: false },
    { name: "仓储服务提供商", arrow: true },
    { name: "关检服务机构：一关三检", arrow: false }
];

services.forEach((svc, idx) => {
    const y = mainY + 0.16 + idx * rowH;
    slide.addShape(pres.shapes.RECTANGLE, {
        x: svcX, y: y, w: svcW, h: svcH,
        fill: { color: theme.secondary }
    });
    slide.addText(svc.name, {
        x: svcX, y: y, w: svcW, h: svcH,
        fontSize: 8, bold: true,
        color: theme.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
    if (svc.arrow) {
        slide.addShape(pres.shapes.LINE, {
            x: svcX + svcW + 0.05, y: y + svcH / 2, w: 0.35, h: 0,
            line: { color: theme.accent, width: 1.5, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
        });
    }
});

// 右侧连接框
const rightX = mainX + 3.45;
const rightItems = [
    { y: 2, h: 0.26, text: "包装、分拣流通加工" },
    { y: 3, h: 0.58, text: "货代、船代、中转\n海、陆、空多式联运" },
    { y: 5, h: 0.26, text: "保税与非保税仓储" }
];

rightItems.forEach(item => {
    const y = mainY + 0.16 + item.y * rowH;
    slide.addShape(pres.shapes.RECTANGLE, {
        x: rightX, y: y, w: 2.3, h: item.h,
        fill: { color: theme.lightGray },
        line: { color: theme.warmGray, width: 1 }
    });
    slide.addText(item.text, {
        x: rightX, y: y, w: 2.3, h: item.h,
        fontSize: 7, bold: true,
        color: theme.textDark, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 向右箭头
slide.addShape(pres.shapes.LINE, {
    x: mainX + mainW + 0.05, y: mainY + 1.2, w: 0.2, h: 0,
    line: { color: theme.accent, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});

// 销售商
slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.85, y: mainY + 0.85, w: 0.8, h: 0.65,
    fill: { color: theme.white },
    line: { color: theme.accent, width: 2.5 }
});
slide.addText("销售商", {
    x: 7.85, y: mainY + 0.85, w: 0.8, h: 0.65,
    fontSize: 11, bold: true,
    color: theme.accent, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 销售商双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 8.7, y: mainY + 1.1, w: 0.18, h: 0,
    line: { color: theme.warmGray, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
});
slide.addShape(pres.shapes.LINE, {
    x: 8.7, y: mainY + 1.28, w: 0.18, h: 0,
    line: { color: theme.warmGray, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 5 }
});

// 客户
slide.addShape(pres.shapes.OVAL, {
    x: 8.95, y: mainY + 0.6, w: 0.9, h: 1.15,
    fill: { color: theme.white },
    line: { color: theme.primary, width: 2.5 }
});
slide.addText("客户/\n需求源", {
    x: 8.95, y: mainY + 0.6, w: 0.9, h: 1.15,
    fontSize: 10, bold: true,
    color: theme.primary, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// === 底部：配套服务提供商 ===
slide.addShape(pres.shapes.LINE, {
    x: 4.9, y: mainY + mainH + 0.03, w: 0, h: 0.18,
    line: { color: theme.accent, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});
slide.addShape(pres.shapes.LINE, {
    x: 5.1, y: mainY + mainH + 0.03, w: 0, h: 0.18,
    line: { color: theme.accent, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});

const bottomY = mainY + mainH + 0.25;
slide.addShape(pres.shapes.RECTANGLE, {
    x: 3, y: bottomY, w: 4, h: 0.6,
    fill: { color: theme.white },
    line: { color: theme.primary, width: 2 }
});
slide.addShape(pres.shapes.RECTANGLE, {
    x: 3, y: bottomY, w: 4, h: 0.08,
    fill: { color: theme.primary }
});
slide.addText("配套服务提供商", {
    x: 3, y: bottomY + 0.15, w: 4, h: 0.3,
    fontSize: 12, bold: true,
    color: theme.primary, align: "center", fontFace: "Microsoft YaHei"
});

const supportItems = ["设计研究所", "银行保险", "劳务公司", "教育培训", "其他服务"];
supportItems.forEach((item, i) => {
    const x = supStartX + i * (supW + supGap);
    slide.addShape(pres.shapes.RECTANGLE, {
        x: x, y: bottomY + 0.75, w: supW, h: 0.22,
        fill: { color: theme.secondary }
    });
    slide.addText(item, {
        x: x, y: bottomY + 0.75, w: supW, h: 0.22,
        fontSize: 7, bold: true,
        color: theme.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// ===== 第3页：核心服务详解 =====
slide = pres.addSlide();
slide.background = { color: theme.lightGray };

// 标题栏
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.7,
    fill: { color: theme.primary }
});
slide.addText("港口物流核心服务", {
    x: 0.5, y: 0.15, w: 9, h: 0.4,
    fontSize: 18, bold: true,
    color: theme.white, align: "left", fontFace: "Microsoft YaHei"
});

// 7个服务卡片 - 2行布局
const serviceList = [
    { name: "引航服务", desc: "拖轮公司提供专业引航", icon: "⚓" },
    { name: "理货服务", desc: "货物清点与记录管理", icon: "📋" },
    { name: "配送服务", desc: "最后一公里配送方案", icon: "🚚" },
    { name: "运输服务", desc: "多式联运整合服务", icon: "🚢" },
    { name: "装卸服务", desc: "高效安全的装卸作业", icon: "🏗️" },
    { name: "仓储服务", desc: "保税与非保税仓储", icon: "🏭" },
    { name: "关检服务", desc: "一关三检通关服务", icon: "🔍" }
];

serviceList.forEach((svc, i) => {
    const row = Math.floor(i / 4);
    const col = i % 4;
    const x = 0.4 + col * 2.4;
    const y = 1 + row * 2.2;
    
    // 卡片背景
    slide.addShape(pres.shapes.RECTANGLE, {
        x: x, y: y, w: 2.2, h: 1.9,
        fill: { color: theme.white },
        line: { color: theme.border, width: 1 }
    });
    
    // 顶部色条
    slide.addShape(pres.shapes.RECTANGLE, {
        x: x, y: y, w: 2.2, h: 0.06,
        fill: { color: i % 2 === 0 ? theme.primary : theme.accent }
    });
    
    // 图标圆圈
    slide.addShape(pres.shapes.OVAL, {
        x: x + 0.75, y: y + 0.25, w: 0.7, h: 0.7,
        fill: { color: i % 2 === 0 ? theme.primary : theme.accent }
    });
    slide.addText(svc.icon, {
        x: x + 0.75, y: y + 0.25, w: 0.7, h: 0.7,
        fontSize: 20,
        color: theme.white, align: "center", valign: "middle"
    });
    
    // 服务名
    slide.addText(svc.name, {
        x: x, y: y + 1.05, w: 2.2, h: 0.35,
        fontSize: 13, bold: true,
        color: theme.textDark, align: "center", fontFace: "Microsoft YaHei"
    });
    
    // 描述
    slide.addText(svc.desc, {
        x: x + 0.1, y: y + 1.4, w: 2, h: 0.4,
        fontSize: 9,
        color: theme.warmGray, align: "center", fontFace: "Microsoft YaHei"
    });
});

// ===== 第4页：总结 =====
slide = pres.addSlide();

// 左侧深海蓝区域
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 4, h: 5.625,
    fill: { color: theme.primary }
});

// 左侧标题
slide.addText("供应链\n核心价值", {
    x: 0.5, y: 1.5, w: 3, h: 1.5,
    fontSize: 28, bold: true,
    color: theme.white, align: "left", fontFace: "Microsoft YaHei"
});

slide.addText("Supply Chain\nCore Value", {
    x: 0.5, y: 3.2, w: 3, h: 1,
    fontSize: 14,
    color: "93C5FD", align: "left", fontFace: "Calibri"
});

// 右侧4个要点
const points = [
    { title: "高效整合", desc: "上下游资源整合\n一站式服务" },
    { title: "成本控制", desc: "优化物流成本\n提升运营效率" },
    { title: "服务质量", desc: "专业化服务\n标准化流程" },
    { title: "客户满意", desc: "快速响应需求\n持续改进优化" }
];

points.forEach((pt, i) => {
    const y = 0.5 + i * 1.3;
    
    // 数字圆圈
    slide.addShape(pres.shapes.OVAL, {
        x: 4.3, y: y, w: 0.5, h: 0.5,
        fill: { color: theme.accent }
    });
    slide.addText(String(i + 1), {
        x: 4.3, y: y, w: 0.5, h: 0.5,
        fontSize: 14, bold: true,
        color: theme.white, align: "center", valign: "middle"
    });
    
    // 标题
    slide.addText(pt.title, {
        x: 5, y: y, w: 4.5, h: 0.35,
        fontSize: 16, bold: true,
        color: theme.primary, align: "left", fontFace: "Microsoft YaHei"
    });
    
    // 描述
    slide.addText(pt.desc, {
        x: 5, y: y + 0.4, w: 4.5, h: 0.6,
        fontSize: 10,
        color: theme.warmGray, align: "left", fontFace: "Microsoft YaHei"
    });
    
    // 分隔线
    if (i < 3) {
        slide.addShape(pres.shapes.LINE, {
            x: 4.3, y: y + 0.9, w: 5.4, h: 0,
            line: { color: theme.border, width: 1 }
        });
    }
});

// 保存
const outputPath = "/root/.openclaw/workspace/港口物流服务供应链_专业版.pptx";
pres.writeFile({ fileName: outputPath });
console.log("专业版PPT已保存: " + outputPath);

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = "港口物流服务供应链";

// 高级配色方案 - 暗色主题+金色强调
const colors = {
    // 背景
    bg: "0F172A",
    bgLight: "1E293B",
    
    // 供应商区 - 暖橙
    supplier: "F97316",
    supplierLight: "FDBA74",
    supplierBg: "7C2D12",
    
    // 核心区 - 深蓝+金
    core: "3B82F6",
    coreLight: "93C5FD",
    coreBg: "1E3A5F",
    gold: "F59E0B",
    goldLight: "FCD34D",
    
    // 客户区 - 青绿
    customer: "10B981",
    customerLight: "6EE7B7",
    customerBg: "064E3B",
    
    // 文字
    text: "F8FAFC",
    textMuted: "94A3B8",
    
    // 线条
    line: "475569",
    arrow: "CBD5E1"
};

// 阴影效果
const shadow = {
    type: 'outer',
    blur: 6,
    offset: 3,
    angle: 45,
    color: "000000",
    opacity: 0.4
};

// ===== 主页面 =====
const slide = pres.addSlide();
slide.background = { color: colors.bg };

// 顶部渐变装饰条
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.08,
    fill: { color: colors.gold }
});

// 标题 - 金色艺术字体
slide.addText("港口物流服务供应链", {
    x: 0, y: 0.2, w: 10, h: 0.6,
    fontSize: 32, bold: true,
    color: colors.gold,
    align: "center",
    fontFace: "Microsoft YaHei",
    shadow: shadow
});
slide.addText("Port Logistics Service Supply Chain", {
    x: 0, y: 0.75, w: 10, h: 0.3,
    fontSize: 12,
    color: colors.textMuted,
    align: "center",
    fontFace: "Arial"
});

// ===== 顶部：物流配给供应商 =====
// 背景面板
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 2, y: 1.1, w: 6, h: 0.8,
    fill: { color: colors.supplierBg },
    line: { color: colors.supplier, width: 2 },
    rectRadius: 0.1
});

slide.addText("物流配给供应商", {
    x: 2, y: 1.15, w: 6, h: 0.3,
    fontSize: 12, bold: true,
    color: colors.supplierLight,
    align: "center",
    fontFace: "Microsoft YaHei"
});

// 5个子项
const topItems = ["港务工程", "修造船厂", "燃料公司", "水电公司", "其他配套"];
topItems.forEach((item, i) => {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 2.2 + i * 1.15, y: 1.5, w: 1.0, h: 0.35,
        fill: { color: colors.supplier },
        rectRadius: 0.05
    });
    slide.addText(item, {
        x: 2.2 + i * 1.15, y: 1.5, w: 1.0, h: 0.35,
        fontSize: 9, bold: true,
        color: colors.bg,
        align: "center", valign: "middle",
        fontFace: "Microsoft YaHei"
    });
});

// 向下箭头
slide.addShape(pres.shapes.LINE, {
    x: 5, y: 1.95, w: 0, h: 0.35,
    line: { color: colors.arrow, width: 3, arrowTypeEnd: 'triangle', arrowSizeEnd: 8 }
});

// ===== 中间核心区 =====
// 主容器
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 1.5, y: 2.35, w: 7, h: 3.2,
    fill: { color: colors.coreBg },
    line: { color: colors.core, width: 3 },
    rectRadius: 0.15
});

// 左侧供应商椭圆
slide.addShape(pres.shapes.OVAL, {
    x: 0.3, y: 3.3, w: 0.9, h: 1.3,
    fill: { color: colors.supplierBg },
    line: { color: colors.supplier, width: 2 }
});
slide.addText("供应商", {
    x: 0.3, y: 3.3, w: 0.9, h: 1.3,
    fontSize: 11, bold: true,
    color: colors.supplierLight,
    align: "center", valign: "middle",
    fontFace: "Microsoft YaHei"
});

// 双向箭头（左侧）
slide.addShape(pres.shapes.LINE, {
    x: 1.25, y: 3.75, w: 0.2, h: 0,
    line: { color: colors.supplier, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});
slide.addShape(pres.shapes.LINE, {
    x: 1.25, y: 3.95, w: 0.2, h: 0,
    line: { color: colors.supplier, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 6 }
});

// 核心区标题
slide.addShape(pres.shapes.RECTANGLE, {
    x: 1.6, y: 2.45, w: 0.5, h: 3.0,
    fill: { color: colors.core }
});
slide.addText("港口物流服务商", {
    x: 1.6, y: 2.5, w: 0.5, h: 2.9,
    fontSize: 13, bold: true,
    color: colors.text,
    align: "center", valign: "middle",
    fontFace: "Microsoft YaHei",
    rotate: 90
});

// 7项服务 - 使用卡片式设计
const services = [
    { name: "引航服务", sub: "拖轮公司", y: 2.55, hasRight: false },
    { name: "理货服务", sub: "理货公司", y: 3.05, hasRight: false },
    { name: "配送服务", sub: "配送提供商", y: 3.55, hasRight: true, rightText: "包装、分拣流通\n加工公司" },
    { name: "运输服务", sub: "运输提供商", y: 4.05, hasRight: true, rightText: "货代、船代、中转\n海陆空联运公司" },
    { name: "装卸服务", sub: "装卸公司", y: 4.55, hasRight: false },
    { name: "仓储服务", sub: "仓储提供商", y: 5.05, hasRight: true, rightText: "保税与非保税\n仓储公司" },
    { name: "关检服务", sub: "一关三检", y: 5.55, hasRight: false }
];

services.forEach(svc => {
    // 主服务卡片
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 2.3, y: svc.y, w: 2.0, h: 0.4,
        fill: { color: colors.bg },
        line: { color: colors.coreLight, width: 1.5 },
        rectRadius: 0.05,
        shadow: shadow
    });
    slide.addText(svc.name, {
        x: 2.3, y: svc.y + 0.02, w: 2.0, h: 0.22,
        fontSize: 10, bold: true,
        color: colors.coreLight,
        align: "center",
        fontFace: "Microsoft YaHei"
    });
    slide.addText(svc.sub, {
        x: 2.3, y: svc.y + 0.22, w: 2.0, h: 0.16,
        fontSize: 7,
        color: colors.textMuted,
        align: "center",
        fontFace: "Microsoft YaHei"
    });
    
    // 向右延伸的服务
    if (svc.hasRight) {
        // 连接线
        slide.addShape(pres.shapes.LINE, {
            x: 4.35, y: svc.y + 0.2, w: 0.4, h: 0,
            line: { color: colors.gold, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
        });
        
        // 延伸卡片
        slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
            x: 4.8, y: svc.y - 0.05, w: 2.2, h: 0.5,
            fill: { color: colors.goldLight, transparency: 20 },
            line: { color: colors.gold, width: 1.5 },
            rectRadius: 0.05
        });
        slide.addText(svc.rightText, {
            x: 4.8, y: svc.y - 0.05, w: 2.2, h: 0.5,
            fontSize: 8,
            color: colors.bg,
            align: "center", valign: "middle",
            fontFace: "Microsoft YaHei"
        });
    }
});

// 右侧销售商
slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.3, y: 3.7, w: 0.6, h: 0.6,
    fill: { color: colors.customerBg },
    line: { color: colors.customer, width: 2 }
});
slide.addText("销售商", {
    x: 7.3, y: 3.7, w: 0.6, h: 0.6,
    fontSize: 10, bold: true,
    color: colors.customerLight,
    align: "center", valign: "middle",
    fontFace: "Microsoft YaHei"
});

// 销售商到客户的双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 7.95, y: 3.95, w: 0.25, h: 0,
    line: { color: colors.customer, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});
slide.addShape(pres.shapes.LINE, {
    x: 7.95, y: 4.15, w: 0.25, h: 0,
    line: { color: colors.customer, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 6 }
});

// 客户椭圆
slide.addShape(pres.shapes.OVAL, {
    x: 8.3, y: 3.55, w: 0.9, h: 0.9,
    fill: { color: colors.customerBg },
    line: { color: colors.customer, width: 2 }
});
slide.addText("客户", {
    x: 8.3, y: 3.55, w: 0.9, h: 0.9,
    fontSize: 11, bold: true,
    color: colors.customerLight,
    align: "center", valign: "middle",
    fontFace: "Microsoft YaHei"
});
slide.addText("需求源", {
    x: 8.3, y: 4.0, w: 0.9, h: 0.4,
    fontSize: 8,
    color: colors.customerLight,
    align: "center",
    fontFace: "Microsoft YaHei"
});

// ===== 底部：配套服务提供商 =====
// 向上箭头
slide.addShape(pres.shapes.LINE, {
    x: 5, y: 5.6, w: 0, h: 0.35,
    line: { color: colors.arrow, width: 3, arrowTypeBegin: 'triangle', arrowSizeBegin: 8 }
});

// 背景面板
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 2, y: 6.0, w: 6, h: 0.8,
    fill: { color: "1E293B" },
    line: { color: colors.textMuted, width: 2 },
    rectRadius: 0.1
});

slide.addText("配套服务提供商", {
    x: 2, y: 6.05, w: 6, h: 0.3,
    fontSize: 12, bold: true,
    color: colors.textMuted,
    align: "center",
    fontFace: "Microsoft YaHei"
});

// 5个子项
const bottomItems = ["设计研究所", "银行保险", "劳务公司", "教育培训", "其他服务"];
bottomItems.forEach((item, i) => {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 2.2 + i * 1.15, y: 6.4, w: 1.0, h: 0.35,
        fill: { color: colors.bgLight },
        line: { color: colors.textMuted, width: 1 },
        rectRadius: 0.05
    });
    slide.addText(item, {
        x: 2.2 + i * 1.15, y: 6.4, w: 1.0, h: 0.35,
        fontSize: 8,
        color: colors.text,
        align: "center", valign: "middle",
        fontFace: "Microsoft YaHei"
    });
});

// 底部装饰条
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 6.92, w: 10, h: 0.08,
    fill: { color: colors.gold }
});

// 保存
const outputPath = "/root/.openclaw/workspace/港口物流服务供应链_艺术版.pptx";
pres.writeFile({ fileName: outputPath });
console.log("艺术版PPT已保存: " + outputPath);

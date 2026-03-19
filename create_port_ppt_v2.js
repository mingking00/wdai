const pptxgen = require("pptxgenjs");

// 创建演示文稿
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = "港口物流服务供应链";
pres.author = "wdai";

// 颜色定义
const colors = {
    primary: "B58900",      // 金棕 - 供应商/销售商
    secondary: "2C3E50",    // 深蓝灰 - 港口物流主体
    accent: "5D737E",       // 中灰蓝 - 配套服务/物流配给
    light: "7F8C8D",        // 浅灰 - 次级服务
    bg: "F8F9FA",          // 背景
    white: "FFFFFF",
    textDark: "212529"
};

// 添加第一页 - 港口物流服务供应链（水平布局）
let slide = pres.addSlide();
slide.background = { color: colors.bg };

// 标题
slide.addText("港口物流服务供应链", {
    x: 0, y: 0.2, w: 10, h: 0.6,
    fontSize: 24, fontFace: "Microsoft YaHei", bold: true,
    color: colors.textDark, align: "center"
});

// ========== 顶部：物流配给供应商 ==========
slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 0.9, w: 3, h: 0.45,
    fill: { color: colors.white },
    line: { color: colors.textDark, width: 1.5 }
});
slide.addText("物流配给供应商", {
    x: 3.5, y: 0.9, w: 3, h: 0.22,
    fontSize: 10, fontFace: "Microsoft YaHei", bold: true,
    color: colors.textDark, align: "center", valign: "middle"
});

// 物流配给子项
const supplies = ["港务工程公司", "修造船厂", "燃料公司", "水电公司", "其他配套"];
supplies.forEach((item, i) => {
    slide.addShape(pres.shapes.RECTANGLE, {
        x: 3.55 + i * 0.58, y: 1.15, w: 0.55, h: 0.18,
        fill: { color: colors.accent }
    });
    slide.addText(item, {
        x: 3.55 + i * 0.58, y: 1.15, w: 0.55, h: 0.18,
        fontSize: 5, fontFace: "Microsoft YaHei",
        color: colors.white, align: "center", valign: "middle"
    });
});

// 箭头：物流配给 → 港口物流
slide.addShape(pres.shapes.LINE, {
    x: 5, y: 1.4, w: 0, h: 0.35,
    line: { color: colors.accent, width: 1.5, arrowEnd: { type: 'triangle', size: 6 } }
});

// ========== 左侧：供应商 ==========
slide.addShape(pres.shapes.OVAL, {
    x: 0.3, y: 2.8, w: 0.8, h: 1.2,
    fill: { color: colors.white },
    line: { color: colors.primary, width: 2 }
});
slide.addText("供应商", {
    x: 0.3, y: 2.8, w: 0.8, h: 1.2,
    fontSize: 11, fontFace: "Microsoft YaHei", bold: true,
    color: colors.primary, align: "center", valign: "middle"
});

// 双向箭头：供应商 ↔ 港口物流
// 左箭头
slide.addShape(pres.shapes.LINE, {
    x: 1.15, y: 3.4, w: 0.35, h: 0,
    line: { color: colors.accent, width: 1.5, arrowBegin: { type: 'triangle', size: 5 } }
});
// 右箭头
slide.addShape(pres.shapes.LINE, {
    x: 1.15, y: 3.25, w: 0.35, h: 0,
    line: { color: colors.accent, width: 1.5, arrowEnd: { type: 'triangle', size: 5 } }
});

// ========== 中间：港口物流服务提供商（主体）==========
const mainX = 1.6;
const mainY = 1.8;
const mainW = 5.8;
const mainH = 3.3;

// 主框
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX, y: mainY, w: mainW, h: mainH,
    fill: { color: colors.white },
    line: { color: colors.secondary, width: 2 }
});

// 竖向标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX + 0.1, y: mainY + 0.8, w: 0.35, h: 1.7,
    fill: { color: colors.secondary }
});
slide.addText("港\n口\n物\n流\n服\n务\n商", {
    x: mainX + 0.1, y: mainY + 0.8, w: 0.35, h: 1.7,
    fontSize: 9, fontFace: "Microsoft YaHei", bold: true,
    color: colors.white, align: "center", valign: "middle"
});

// 内部服务项（左列）
const leftServices = [
    {name: "引航服务提供商：拖轮公司", hasArrow: false},
    {name: "理货服务提供商：理货公司", hasArrow: false},
    {name: "配送服务提供商", hasArrow: true, arrowTo: "包装分拣"},
    {name: "运输服务提供商", hasArrow: true, arrowTo: "货代多式联运"},
    {name: "装卸服务提供商：装卸公司", hasArrow: false},
    {name: "仓储服务提供商", hasArrow: true, arrowTo: "保税仓储"},
    {name: "关检服务机构：一关三检", hasArrow: false}
];

leftServices.forEach((svc, i) => {
    const y = mainY + 0.25 + i * 0.42;
    
    // 服务框
    slide.addShape(pres.shapes.RECTANGLE, {
        x: mainX + 0.55, y: y, w: 2.2, h: 0.35,
        fill: { color: colors.secondary }
    });
    slide.addText(svc.name, {
        x: mainX + 0.55, y: y, w: 2.2, h: 0.35,
        fontSize: 7, fontFace: "Microsoft YaHei",
        color: colors.white, align: "center", valign: "middle"
    });
    
    // 如果有向右的箭头
    if (svc.hasArrow) {
        slide.addShape(pres.shapes.LINE, {
            x: mainX + 2.8, y: y + 0.175, w: 0.4, h: 0,
            line: { color: colors.accent, width: 1, arrowEnd: { type: 'triangle', size: 4 } }
        });
    }
});

// 右侧连接的服务
// 包装分拣
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX + 3.25, y: mainY + 0.9, w: 2.3, h: 0.35,
    fill: { color: colors.light }
});
slide.addText("包装、分拣流通加工公司", {
    x: mainX + 3.25, y: mainY + 0.9, w: 2.3, h: 0.35,
    fontSize: 7, fontFace: "Microsoft YaHei",
    color: colors.white, align: "center", valign: "middle"
});

// 货代多式联运
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX + 3.25, y: mainY + 1.55, w: 2.3, h: 0.35,
    fill: { color: colors.light }
});
slide.addText("货代、船代、中转公司\n海、陆、空多式联运公司", {
    x: mainX + 3.25, y: mainY + 1.55, w: 2.3, h: 0.35,
    fontSize: 6, fontFace: "Microsoft YaHei",
    color: colors.white, align: "center", valign: "middle"
});

// 保税仓储
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX + 3.25, y: mainY + 2.75, w: 2.3, h: 0.35,
    fill: { color: colors.light }
});
slide.addText("保税与非保税仓储公司", {
    x: mainX + 3.25, y: mainY + 2.75, w: 2.3, h: 0.35,
    fontSize: 7, fontFace: "Microsoft YaHei",
    color: colors.white, align: "center", valign: "middle"
});

// ========== 右侧：销售商 ==========
slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.6, y: 3.2, w: 0.6, h: 0.7,
    fill: { color: colors.white },
    line: { color: colors.primary, width: 2 }
});
slide.addText("销售商", {
    x: 7.6, y: 3.2, w: 0.6, h: 0.7,
    fontSize: 10, fontFace: "Microsoft YaHei", bold: true,
    color: colors.primary, align: "center", valign: "middle"
});

// 箭头：港口物流 → 销售商
slide.addShape(pres.shapes.LINE, {
    x: 7.45, y: 3.35, w: 0.1, h: 0,
    line: { color: colors.accent, width: 1.5, arrowEnd: { type: 'triangle', size: 5 } }
});

// ========== 最右侧：客户/需求源 ==========
slide.addShape(pres.shapes.OVAL, {
    x: 8.5, y: 2.8, w: 0.8, h: 1.2,
    fill: { color: colors.white },
    line: { color: colors.secondary, width: 2 }
});
slide.addText("客户/\n需求源", {
    x: 8.5, y: 2.8, w: 0.8, h: 1.2,
    fontSize: 10, fontFace: "Microsoft YaHei", bold: true,
    color: colors.secondary, align: "center", valign: "middle"
});

// 双向箭头：销售商 ↔ 客户
// 左箭头
slide.addShape(pres.shapes.LINE, {
    x: 8.25, y: 3.4, w: 0.2, h: 0,
    line: { color: colors.accent, width: 1.5, arrowBegin: { type: 'triangle', size: 5 } }
});
// 右箭头
slide.addShape(pres.shapes.LINE, {
    x: 8.25, y: 3.25, w: 0.2, h: 0,
    line: { color: colors.accent, width: 1.5, arrowEnd: { type: 'triangle', size: 5 } }
});

// ========== 底部：配套服务提供商 ==========
// 向上箭头
slide.addShape(pres.shapes.LINE, {
    x: 5, y: 5.15, w: 0, h: 0.35,
    line: { color: colors.accent, width: 1.5, arrowEnd: { type: 'triangle', size: 6 } }
});

slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 5.55, w: 3, h: 0.45,
    fill: { color: colors.white },
    line: { color: colors.textDark, width: 1.5 }
});
slide.addText("配套服务提供商", {
    x: 3.5, y: 5.55, w: 3, h: 0.22,
    fontSize: 10, fontFace: "Microsoft YaHei", bold: true,
    color: colors.textDark, align: "center", valign: "middle"
});

// 配套服务子项
const supportServices = ["设计研究所", "银行保险", "劳务公司", "教育培训", "其他服务"];
supportServices.forEach((item, i) => {
    slide.addShape(pres.shapes.RECTANGLE, {
        x: 3.55 + i * 0.58, y: 5.8, w: 0.55, h: 0.18,
        fill: { color: colors.accent }
    });
    slide.addText(item, {
        x: 3.55 + i * 0.58, y: 5.8, w: 0.55, h: 0.18,
        fontSize: 5, fontFace: "Microsoft YaHei",
        color: colors.white, align: "center", valign: "middle"
    });
});

// 保存文件
pres.writeFile({ fileName: "/root/.openclaw/workspace/港口物流服务供应链.pptx" });
console.log("PPT 已保存（修正版）: /root/.openclaw/workspace/港口物流服务供应链.pptx");

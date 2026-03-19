const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = "港口物流服务供应链";

const colors = {
    primary: "B58900",
    secondary: "2C3E50",
    accent: "5D737E",
    light: "7F8C8D",
    bg: "F8F9FA",
    white: "FFFFFF",
    textDark: "212529"
};

let slide = pres.addSlide();
slide.background = { color: colors.bg };

// 标题
slide.addText("港口物流服务供应链", {
    x: 0, y: 0.1, w: 10, h: 0.5,
    fontSize: 22, fontFace: "Microsoft YaHei", bold: true,
    color: colors.textDark, align: "center"
});

// ========== 顶部：物流配给供应商 ==========
const topBoxY = 0.75;
slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.2, y: topBoxY, w: 3.6, h: 0.65,
    fill: { color: colors.white },
    line: { color: colors.textDark, width: 2 }
});
slide.addText("物流配给供应商", {
    x: 3.2, y: topBoxY + 0.05, w: 3.6, h: 0.2,
    fontSize: 10, fontFace: "Microsoft YaHei", bold: true,
    color: colors.textDark, align: "center"
});

const supplies = ["港务工程公司", "修造船厂", "燃料公司", "水电公司", "其他配套"];
supplies.forEach((item, i) => {
    const boxW = 0.65;
    const gap = 0.05;
    const startX = 3.25 + i * (boxW + gap);
    slide.addShape(pres.shapes.RECTANGLE, {
        x: startX, y: topBoxY + 0.3, w: boxW, h: 0.28,
        fill: { color: colors.accent }
    });
    slide.addText(item, {
        x: startX, y: topBoxY + 0.3, w: boxW, h: 0.28,
        fontSize: 6, fontFace: "Microsoft YaHei",
        color: colors.white, align: "center", valign: "middle"
    });
});

// 向下箭头（双箭头）
slide.addShape(pres.shapes.LINE, {
    x: 5, y: 1.45, w: 0, h: 0.3,
    line: { color: "2C3E50", width: 2, arrowEnd: { type: 'triangle', size: 6 } }
});
slide.addShape(pres.shapes.LINE, {
    x: 4.85, y: 1.45, w: 0, h: 0.3,
    line: { color: "2C3E50", width: 2, arrowEnd: { type: 'triangle', size: 6 } }
});

// ========== 中间主体区域 ==========
const mainY = 1.8;
const mainH = 3.0;

// 左侧：供应商（椭圆）
slide.addShape(pres.shapes.OVAL, {
    x: 0.2, y: mainY + 0.8, w: 0.9, h: 1.4,
    fill: { color: colors.white },
    line: { color: colors.primary, width: 2 }
});
slide.addText("供应商", {
    x: 0.2, y: mainY + 0.8, w: 0.9, h: 1.4,
    fontSize: 12, fontFace: "Microsoft YaHei", bold: true,
    color: colors.primary, align: "center", valign: "middle"
});

// 双向箭头：供应商 ↔ 港口物流
// 向右箭头
slide.addShape(pres.shapes.LINE, {
    x: 1.15, y: mainY + 1.35, w: 0.3, h: 0,
    line: { color: "2C3E50", width: 2, arrowEnd: { type: 'triangle', size: 5 } }
});
// 向左箭头（在下方）
slide.addShape(pres.shapes.LINE, {
    x: 1.15, y: mainY + 1.6, w: 0.3, h: 0,
    line: { color: "2C3E50", width: 2, arrowBegin: { type: 'triangle', size: 5 } }
});

// 港口物流主体框
const mainX = 1.5;
const mainW = 6.0;
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX, y: mainY, w: mainW, h: mainH,
    fill: { color: colors.white },
    line: { color: colors.secondary, width: 3 }
});

// 竖向标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX + 0.1, y: mainY + 0.6, w: 0.4, h: 1.8,
    fill: { color: colors.secondary }
});
slide.addText("港\n口\n物\n流\n服\n务\n商", {
    x: mainX + 0.1, y: mainY + 0.6, w: 0.4, h: 1.8,
    fontSize: 10, fontFace: "Microsoft YaHei", bold: true,
    color: colors.white, align: "center", valign: "middle"
});

// 左侧服务列表
const services = [
    {name: "引航服务提供商：拖轮公司", y: 0},
    {name: "理货服务提供商：理货公司", y: 1},
    {name: "配送服务提供商", y: 2, hasArrow: true},
    {name: "运输服务提供商", y: 3, hasArrow: true},
    {name: "装卸服务提供商：装卸公司", y: 4},
    {name: "仓储服务提供商", y: 5, hasArrow: true},
    {name: "关检服务机构：一关三检", y: 6}
];

const leftX = mainX + 0.6;
const svcBoxW = 2.4;
const svcBoxH = 0.32;
const rowHeight = 0.38;

services.forEach((svc) => {
    const y = mainY + 0.25 + svc.y * rowHeight;
    
    slide.addShape(pres.shapes.RECTANGLE, {
        x: leftX, y: y, w: svcBoxW, h: svcBoxH,
        fill: { color: colors.secondary }
    });
    slide.addText(svc.name, {
        x: leftX, y: y, w: svcBoxW, h: svcBoxH,
        fontSize: 8, fontFace: "Microsoft YaHei",
        color: colors.white, align: "center", valign: "middle"
    });
    
    if (svc.hasArrow) {
        slide.addShape(pres.shapes.LINE, {
            x: leftX + svcBoxW + 0.05, y: y + svcBoxH/2, w: 0.35, h: 0,
            line: { color: "2C3E50", width: 1.5, arrowEnd: { type: 'triangle', size: 4 } }
        });
    }
});

// 右侧连接框
const rightX = mainX + 3.5;
const rightItems = [
    {text: "包装、分拣流通加工公司", y: 2},
    {text: "货代、船代、中转公司\n海、陆、空多式联运公司", y: 3, small: true},
    {text: "保税与非保税仓储公司", y: 5}
];

rightItems.forEach((item) => {
    const y = mainY + 0.25 + item.y * rowHeight;
    const h = item.small ? 0.32 : 0.32;
    
    slide.addShape(pres.shapes.RECTANGLE, {
        x: rightX, y: y, w: 2.3, h: h,
        fill: { color: colors.light }
    });
    slide.addText(item.text, {
        x: rightX, y: y, w: 2.3, h: h,
        fontSize: item.small ? 6 : 7, fontFace: "Microsoft YaHei",
        color: colors.white, align: "center", valign: "middle"
    });
});

// 向右箭头：港口物流 → 销售商
slide.addShape(pres.shapes.LINE, {
    x: mainX + mainW + 0.05, y: mainY + 1.5, w: 0.35, h: 0,
    line: { color: "2C3E50", width: 2, arrowEnd: { type: 'triangle', size: 5 } }
});

// 销售商
slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.6, y: mainY + 1.2, w: 0.7, h: 0.7,
    fill: { color: colors.white },
    line: { color: colors.primary, width: 2 }
});
slide.addText("销售商", {
    x: 7.6, y: mainY + 1.2, w: 0.7, h: 0.7,
    fontSize: 10, fontFace: "Microsoft YaHei", bold: true,
    color: colors.primary, align: "center", valign: "middle"
});

// 双向箭头：销售商 ↔ 客户
// 向右箭头
slide.addShape(pres.shapes.LINE, {
    x: 8.35, y: mainY + 1.45, w: 0.25, h: 0,
    line: { color: "2C3E50", width: 2, arrowEnd: { type: 'triangle', size: 5 } }
});
// 向左箭头
slide.addShape(pres.shapes.LINE, {
    x: 8.35, y: mainY + 1.65, w: 0.25, h: 0,
    line: { color: "2C3E50", width: 2, arrowBegin: { type: 'triangle', size: 5 } }
});

// 客户/需求源
slide.addShape(pres.shapes.OVAL, {
    x: 8.7, y: mainY + 0.9, w: 0.9, h: 1.3,
    fill: { color: colors.white },
    line: { color: colors.secondary, width: 2 }
});
slide.addText("客户/\n需求源", {
    x: 8.7, y: mainY + 0.9, w: 0.9, h: 1.3,
    fontSize: 11, fontFace: "Microsoft YaHei", bold: true,
    color: colors.secondary, align: "center", valign: "middle"
});

// ========== 底部：配套服务提供商 ==========
// 向上箭头（双箭头）
slide.addShape(pres.shapes.LINE, {
    x: 5, y: mainY + mainH + 0.1, w: 0, h: 0.3,
    line: { color: "2C3E50", width: 2, arrowEnd: { type: 'triangle', size: 6 } }
});
slide.addShape(pres.shapes.LINE, {
    x: 4.85, y: mainY + mainH + 0.1, w: 0, h: 0.3,
    line: { color: "2C3E50", width: 2, arrowEnd: { type: 'triangle', size: 6 } }
});

const bottomY = mainY + mainH + 0.5;
slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.2, y: bottomY, w: 3.6, h: 0.65,
    fill: { color: colors.white },
    line: { color: colors.textDark, width: 2 }
});
slide.addText("配套服务提供商", {
    x: 3.2, y: bottomY + 0.05, w: 3.6, h: 0.2,
    fontSize: 10, fontFace: "Microsoft YaHei", bold: true,
    color: colors.textDark, align: "center"
});

const supportServices = ["设计研究所", "银行保险", "劳务公司", "教育培训", "其他服务"];
supportServices.forEach((item, i) => {
    const boxW = 0.65;
    const gap = 0.05;
    const startX = 3.25 + i * (boxW + gap);
    slide.addShape(pres.shapes.RECTANGLE, {
        x: startX, y: bottomY + 0.3, w: boxW, h: 0.28,
        fill: { color: colors.accent }
    });
    slide.addText(item, {
        x: startX, y: bottomY + 0.3, w: boxW, h: 0.28,
        fontSize: 6, fontFace: "Microsoft YaHei",
        color: colors.white, align: "center", valign: "middle"
    });
});

pres.writeFile({ fileName: "/root/.openclaw/workspace/港口物流服务供应链.pptx" });
console.log("PPT 已更新: /root/.openclaw/workspace/港口物流服务供应链.pptx");

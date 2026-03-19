const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = "港口物流服务供应链";

// Midnight Executive 主题配色
const theme = {
    primary: "1E2761",
    secondary: "CADCFC",
    accent: "FFFFFF",
    gold: "D4AF37",
    slate: "4A5568",
    silver: "A0AEC0",
    bg: "0F172A",
    card: "1E293B",
    line: "60A5FA"
};

let slide = pres.addSlide();

// 背景
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { color: theme.bg }
});

// 顶部装饰条
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.08,
    fill: { color: theme.gold }
});

// 标题 - 第1个出现
slide.addText("港口物流服务供应链", {
    x: 0, y: 0.25, w: 10, h: 0.6,
    fontSize: 36, bold: true,
    color: theme.accent, align: "center", fontFace: "Microsoft YaHei"
});

// 副标题
slide.addText("Port Logistics Service Supply Chain", {
    x: 0, y: 0.85, w: 10, h: 0.3,
    fontSize: 12, italic: true,
    color: theme.silver, align: "center", fontFace: "Calibri"
});

// ========== 顶部：物流配给供应商 - 第2个出现 ==========
const topY = 1.25;
const topW = 4.2;
const topX = 2.9;

slide.addShape(pres.shapes.RECTANGLE, {
    x: topX - 0.02, y: topY - 0.02, w: topW + 0.04, h: 0.74,
    fill: { color: theme.gold }
});
slide.addShape(pres.shapes.RECTANGLE, {
    x: topX, y: topY, w: topW, h: 0.7,
    fill: { color: theme.card }
});

slide.addText("物流配给供应商", {
    x: topX, y: topY + 0.08, w: topW, h: 0.25,
    fontSize: 12, bold: true,
    color: theme.gold, align: "center", fontFace: "Microsoft YaHei"
});

const supW = 0.72;
const supGap = 0.1;
const supStartX = 3.05;

const supplies = ["港务工程", "修造船厂", "燃料公司", "水电公司", "其他配套"];
supplies.forEach((item, i) => {
    const x = supStartX + i * (supW + supGap);
    slide.addShape(pres.shapes.RECTANGLE, {
        x: x, y: topY + 0.38, w: supW, h: 0.26,
        fill: { color: theme.slate }
    });
    slide.addText(item, {
        x: x, y: topY + 0.38, w: supW, h: 0.26,
        fontSize: 8, bold: true,
        color: theme.accent, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 向下箭头
slide.addShape(pres.shapes.LINE, {
    x: 4.85, y: 2.0, w: 0, h: 0.28,
    line: { color: theme.gold, width: 3, arrowTypeEnd: 'triangle', arrowSizeEnd: 8 }
});
slide.addShape(pres.shapes.LINE, {
    x: 5.15, y: 2.0, w: 0, h: 0.28,
    line: { color: theme.gold, width: 3, arrowTypeEnd: 'triangle', arrowSizeEnd: 8 }
});

// ========== 中间主体 ==========
const mainY = 2.35;
const mainH = 2.4;
const mainX = 1.4;
const mainW = 6.0;

// 供应商椭圆 - 第3个出现
slide.addShape(pres.shapes.OVAL, {
    x: 0.25, y: mainY + 0.55, w: 0.9, h: 1.2,
    fill: { color: theme.card },
    line: { color: theme.gold, width: 3 }
});
slide.addText("供应商", {
    x: 0.25, y: mainY + 0.55, w: 0.9, h: 1.2,
    fontSize: 14, bold: true,
    color: theme.gold, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 1.2, y: mainY + 1.0, w: 0.15, h: 0,
    line: { color: theme.line, width: 2.5, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});
slide.addShape(pres.shapes.LINE, {
    x: 1.2, y: mainY + 1.2, w: 0.15, h: 0,
    line: { color: theme.line, width: 2.5, arrowTypeBegin: 'triangle', arrowSizeBegin: 6 }
});

// 港口物流主框 - 第4个出现
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX - 0.03, y: mainY - 0.03, w: mainW + 0.06, h: mainH + 0.06,
    fill: { color: theme.line }
});
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX, y: mainY, w: mainW, h: mainH,
    fill: { color: theme.card }
});

// 竖向标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX + 0.12, y: mainY + 0.5, w: 0.4, h: 1.4,
    fill: { color: theme.primary }
});
slide.addText("港\n口\n物\n流\n服\n务\n商", {
    x: mainX + 0.12, y: mainY + 0.5, w: 0.4, h: 1.4,
    fontSize: 11, bold: true,
    color: theme.accent, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 左侧服务项 - 第5个出现（逐个）
const svcX = mainX + 0.6;
const svcW = 2.3;
const svcH = 0.28;
const rowH = 0.32;

const services = [
    {name: "引航服务：拖轮公司", y: 0, arrow: false},
    {name: "理货服务：理货公司", y: 1, arrow: false},
    {name: "配送服务提供商", y: 2, arrow: true},
    {name: "运输服务提供商", y: 3, arrow: true},
    {name: "装卸服务：装卸公司", y: 4, arrow: false},
    {name: "仓储服务提供商", y: 5, arrow: true},
    {name: "关检：一关三检", y: 6, arrow: false}
];

services.forEach((svc) => {
    const y = mainY + 0.18 + svc.y * rowH;
    
    slide.addShape(pres.shapes.RECTANGLE, {
        x: svcX, y: y, w: svcW, h: svcH,
        fill: { color: theme.primary }
    });
    slide.addText(svc.name, {
        x: svcX, y: y, w: svcW, h: svcH,
        fontSize: 8, bold: true,
        color: theme.accent, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
    
    if (svc.arrow) {
        slide.addShape(pres.shapes.LINE, {
            x: svcX + svcW + 0.08, y: y + svcH/2, w: 0.35, h: 0,
            line: { color: theme.line, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
        });
    }
});

// 右侧连接框 - 第6个出现
const rightX = mainX + 3.3;

slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: mainY + 0.18 + 2 * rowH, w: 2.3, h: 0.28,
    fill: { color: theme.silver }
});
slide.addText("包装、分拣流通加工", {
    x: rightX, y: mainY + 0.18 + 2 * rowH, w: 2.3, h: 0.28,
    fontSize: 8, bold: true,
    color: theme.primary, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: mainY + 0.18 + 3 * rowH, w: 2.3, h: 0.58,
    fill: { color: theme.silver }
});
slide.addText("货代、船代、中转\n海、陆、空多式联运", {
    x: rightX, y: mainY + 0.18 + 3 * rowH, w: 2.3, h: 0.58,
    fontSize: 7, bold: true,
    color: theme.primary, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: mainY + 0.18 + 5 * rowH, w: 2.3, h: 0.28,
    fill: { color: theme.silver }
});
slide.addText("保税与非保税仓储", {
    x: rightX, y: mainY + 0.18 + 5 * rowH, w: 2.3, h: 0.28,
    fontSize: 8, bold: true,
    color: theme.primary, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 向右箭头
slide.addShape(pres.shapes.LINE, {
    x: mainX + mainW + 0.08, y: mainY + 1.2, w: 0.25, h: 0,
    line: { color: theme.line, width: 2.5, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});

// 销售商 - 第7个出现
slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.75, y: mainY + 0.9, w: 0.8, h: 0.7,
    fill: { color: theme.card },
    line: { color: theme.gold, width: 3 }
});
slide.addText("销售商", {
    x: 7.75, y: mainY + 0.9, w: 0.8, h: 0.7,
    fontSize: 12, bold: true,
    color: theme.gold, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 销售商双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 8.6, y: mainY + 1.15, w: 0.2, h: 0,
    line: { color: theme.line, width: 2.5, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});
slide.addShape(pres.shapes.LINE, {
    x: 8.6, y: mainY + 1.35, w: 0.2, h: 0,
    line: { color: theme.line, width: 2.5, arrowTypeBegin: 'triangle', arrowSizeBegin: 6 }
});

// 客户 - 第8个出现
slide.addShape(pres.shapes.OVAL, {
    x: 8.9, y: mainY + 0.65, w: 0.9, h: 1.15,
    fill: { color: theme.card },
    line: { color: theme.primary, width: 3 }
});
slide.addText("客户/\n需求源", {
    x: 8.9, y: mainY + 0.65, w: 0.9, h: 1.15,
    fontSize: 11, bold: true,
    color: theme.accent, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// ========== 底部：配套服务提供商 - 第9个出现 ==========
slide.addShape(pres.shapes.LINE, {
    x: 4.85, y: mainY + mainH + 0.05, w: 0, h: 0.25,
    line: { color: theme.gold, width: 3, arrowTypeEnd: 'triangle', arrowSizeEnd: 8 }
});
slide.addShape(pres.shapes.LINE, {
    x: 5.15, y: mainY + mainH + 0.05, w: 0, h: 0.25,
    line: { color: theme.gold, width: 3, arrowTypeEnd: 'triangle', arrowSizeEnd: 8 }
});

const bottomY = mainY + mainH + 0.35;

slide.addShape(pres.shapes.RECTANGLE, {
    x: topX - 0.02, y: bottomY - 0.02, w: topW + 0.04, h: 0.74,
    fill: { color: theme.gold }
});
slide.addShape(pres.shapes.RECTANGLE, {
    x: topX, y: bottomY, w: topW, h: 0.7,
    fill: { color: theme.card }
});
slide.addText("配套服务提供商", {
    x: topX, y: bottomY + 0.08, w: topW, h: 0.25,
    fontSize: 12, bold: true,
    color: theme.gold, align: "center", fontFace: "Microsoft YaHei"
});

const supportServices = ["设计研究所", "银行保险", "劳务公司", "教育培训", "其他服务"];
supportServices.forEach((item, i) => {
    const x = supStartX + i * (supW + supGap);
    slide.addShape(pres.shapes.RECTANGLE, {
        x: x, y: bottomY + 0.38, w: supW, h: 0.26,
        fill: { color: theme.slate }
    });
    slide.addText(item, {
        x: x, y: bottomY + 0.38, w: supW, h: 0.26,
        fontSize: 8, bold: true,
        color: theme.accent, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 底部装饰条
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.545, w: 10, h: 0.08,
    fill: { color: theme.gold }
});

// 保存
const outputPath = "/root/.openclaw/workspace/港口物流服务供应链_动画版.pptx";
pres.writeFile({ fileName: outputPath });
console.log("动画版PPT已保存: " + outputPath);

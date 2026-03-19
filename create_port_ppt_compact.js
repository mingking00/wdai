const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = "港口物流服务供应链";

const colors = {
    navy: "1A2B3C",
    slate: "3D5A73",
    gold: "C9A227",
    steel: "5C7A8A",
    silver: "8FA3B0",
    white: "FFFFFF",
    bg: "F5F7FA",
    line: "2C3E50"
};

let slide = pres.addSlide();
slide.background = { color: colors.bg };

// 标题 - 缩小
slide.addText("港口物流服务供应链", {
    x: 0, y: 0.1, w: 10, h: 0.45,
    fontSize: 24, bold: true,
    color: colors.navy, align: "center", fontFace: "Microsoft YaHei"
});

// ========== 顶部：物流配给供应商 ==========
const topY = 0.55;
const topW = 4.0;
const topX = 3.0;

slide.addShape(pres.shapes.RECTANGLE, {
    x: topX, y: topY, w: topW, h: 0.7,
    fill: { color: colors.white },
    line: { color: colors.steel, width: 1.5 }
});

slide.addText("物流配给供应商", {
    x: topX, y: topY + 0.05, w: topW, h: 0.22,
    fontSize: 11, bold: true,
    color: colors.navy, align: "center", fontFace: "Microsoft YaHei"
});

const supW = 0.7;
const supGap = 0.08;
const supStartX = 3.15;

const supplies = ["港务工程公司", "修造船厂", "燃料公司", "水电公司", "其他配套"];
supplies.forEach((item, i) => {
    const x = supStartX + i * (supW + supGap);
    slide.addShape(pres.shapes.RECTANGLE, {
        x: x, y: topY + 0.32, w: supW, h: 0.28,
        fill: { color: colors.steel }
    });
    slide.addText(item, {
        x: x, y: topY + 0.32, w: supW, h: 0.28,
        fontSize: 7, bold: true,
        color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 向下双箭头
slide.addShape(pres.shapes.LINE, {
    x: 4.9, y: 1.28, w: 0, h: 0.25,
    line: { color: colors.line, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});
slide.addShape(pres.shapes.LINE, {
    x: 5.1, y: 1.28, w: 0, h: 0.25,
    line: { color: colors.line, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});

// ========== 中间主体 ==========
const mainY = 1.55;
const mainH = 2.6;
const mainX = 1.5;
const mainW = 6.0;

// 供应商椭圆 - 缩小
slide.addShape(pres.shapes.OVAL, {
    x: 0.3, y: mainY + 0.6, w: 0.8, h: 1.2,
    fill: { color: colors.white },
    line: { color: colors.gold, width: 2 }
});
slide.addText("供应商", {
    x: 0.3, y: mainY + 0.6, w: 0.8, h: 1.2,
    fontSize: 12, bold: true,
    color: colors.gold, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 1.15, y: mainY + 1.1, w: 0.25, h: 0,
    line: { color: colors.line, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
});
slide.addShape(pres.shapes.LINE, {
    x: 1.15, y: mainY + 1.3, w: 0.25, h: 0,
    line: { color: colors.line, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 5 }
});

// 港口物流主框
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX, y: mainY, w: mainW, h: mainH,
    fill: { color: colors.white },
    line: { color: colors.navy, width: 2 }
});

// 竖向标签 - 缩小
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX + 0.1, y: mainY + 0.5, w: 0.35, h: 1.6,
    fill: { color: colors.navy }
});
slide.addText("港\n口\n物\n流\n服\n务\n商", {
    x: mainX + 0.1, y: mainY + 0.5, w: 0.35, h: 1.6,
    fontSize: 10, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 左侧服务项 - 缩小
const svcX = mainX + 0.55;
const svcW = 2.2;
const svcH = 0.3;
const rowH = 0.34;

const services = [
    {name: "引航服务提供商：拖轮公司", y: 0, arrow: false},
    {name: "理货服务提供商：理货公司", y: 1, arrow: false},
    {name: "配送服务提供商", y: 2, arrow: true},
    {name: "运输服务提供商", y: 3, arrow: true},
    {name: "装卸服务提供商：装卸公司", y: 4, arrow: false},
    {name: "仓储服务提供商", y: 5, arrow: true},
    {name: "关检服务机构：一关三检", y: 6, arrow: false}
];

services.forEach((svc) => {
    const y = mainY + 0.15 + svc.y * rowH;
    
    slide.addShape(pres.shapes.RECTANGLE, {
        x: svcX, y: y, w: svcW, h: svcH,
        fill: { color: colors.slate }
    });
    slide.addText(svc.name, {
        x: svcX, y: y, w: svcW, h: svcH,
        fontSize: 8, bold: true,
        color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
    
    if (svc.arrow) {
        slide.addShape(pres.shapes.LINE, {
            x: svcX + svcW + 0.08, y: y + svcH/2, w: 0.4, h: 0,
            line: { color: colors.line, width: 1.5, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
        });
    }
});

// 右侧连接框 - 缩小
const rightX = mainX + 3.2;

slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: mainY + 0.15 + 2 * rowH, w: 2.2, h: 0.3,
    fill: { color: colors.silver }
});
slide.addText("包装、分拣流通加工公司", {
    x: rightX, y: mainY + 0.15 + 2 * rowH, w: 2.2, h: 0.3,
    fontSize: 8, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: mainY + 0.15 + 3 * rowH, w: 2.2, h: 0.6,
    fill: { color: colors.silver }
});
slide.addText("货代、船代、中转公司\n海、陆、空多式联运", {
    x: rightX, y: mainY + 0.15 + 3 * rowH, w: 2.2, h: 0.6,
    fontSize: 7, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: mainY + 0.15 + 5 * rowH, w: 2.2, h: 0.3,
    fill: { color: colors.silver }
});
slide.addText("保税与非保税仓储公司", {
    x: rightX, y: mainY + 0.15 + 5 * rowH, w: 2.2, h: 0.3,
    fontSize: 8, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 向右箭头
slide.addShape(pres.shapes.LINE, {
    x: mainX + mainW + 0.08, y: mainY + 1.3, w: 0.25, h: 0,
    line: { color: colors.line, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
});

// 销售商 - 缩小
slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.85, y: mainY + 1.0, w: 0.75, h: 0.75,
    fill: { color: colors.white },
    line: { color: colors.gold, width: 2 }
});
slide.addText("销售商", {
    x: 7.85, y: mainY + 1.0, w: 0.75, h: 0.75,
    fontSize: 11, bold: true,
    color: colors.gold, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 销售商双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 8.65, y: mainY + 1.25, w: 0.25, h: 0,
    line: { color: colors.line, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
});
slide.addShape(pres.shapes.LINE, {
    x: 8.65, y: mainY + 1.45, w: 0.25, h: 0,
    line: { color: colors.line, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 5 }
});

// 客户 - 缩小
slide.addShape(pres.shapes.OVAL, {
    x: 9.0, y: mainY + 0.7, w: 0.85, h: 1.2,
    fill: { color: colors.white },
    line: { color: colors.navy, width: 2 }
});
slide.addText("客户/\n需求源", {
    x: 9.0, y: mainY + 0.7, w: 0.85, h: 1.2,
    fontSize: 10, bold: true,
    color: colors.navy, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// ========== 底部：配套服务提供商 ==========
slide.addShape(pres.shapes.LINE, {
    x: 4.9, y: mainY + mainH + 0.05, w: 0, h: 0.25,
    line: { color: colors.line, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});
slide.addShape(pres.shapes.LINE, {
    x: 5.1, y: mainY + mainH + 0.05, w: 0, h: 0.25,
    line: { color: colors.line, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});

const bottomY = mainY + mainH + 0.35;

slide.addShape(pres.shapes.RECTANGLE, {
    x: topX, y: bottomY, w: topW, h: 0.7,
    fill: { color: colors.white },
    line: { color: colors.steel, width: 1.5 }
});
slide.addText("配套服务提供商", {
    x: topX, y: bottomY + 0.05, w: topW, h: 0.22,
    fontSize: 11, bold: true,
    color: colors.navy, align: "center", fontFace: "Microsoft YaHei"
});

const supportServices = ["设计研究所", "银行保险", "劳务公司", "教育培训", "其他服务"];
supportServices.forEach((item, i) => {
    const x = supStartX + i * (supW + supGap);
    slide.addShape(pres.shapes.RECTANGLE, {
        x: x, y: bottomY + 0.32, w: supW, h: 0.28,
        fill: { color: colors.steel }
    });
    slide.addText(item, {
        x: x, y: bottomY + 0.32, w: supW, h: 0.28,
        fontSize: 7, bold: true,
        color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 保存
const outputPath = "/root/.openclaw/workspace/港口物流服务供应链_v3.pptx";
pres.writeFile({ fileName: outputPath });
console.log("PPT 已保存: " + outputPath);

const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = "港口物流服务供应链";

// 高级配色
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

// 添加渐变背景
slide.background = {
    color: colors.bg
};

// 标题
slide.addText("港口物流服务供应链", {
    x: 0, y: 0.15, w: 10, h: 0.6,
    fontSize: 32, bold: true,
    color: colors.navy, align: "center", fontFace: "Microsoft YaHei"
});

// 金色分隔线
slide.addShape(pres.shapes.RECTANGLE, {
    x: 4.2, y: 0.75, w: 1.6, h: 0.04,
    fill: { color: colors.gold }
});

// ========== 顶部：物流配给供应商 ==========
const topY = 0.95;
const topW = 4.5;
const topX = 2.75;

slide.addShape(pres.shapes.RECTANGLE, {
    x: topX, y: topY, w: topW, h: 0.9,
    fill: { color: colors.white },
    line: { color: colors.steel, width: 2 }
});

slide.addText("物流配给供应商", {
    x: topX, y: topY + 0.08, w: topW, h: 0.3,
    fontSize: 14, bold: true,
    color: colors.navy, align: "center", fontFace: "Microsoft YaHei"
});

// 分隔线
slide.addShape(pres.shapes.RECTANGLE, {
    x: topX + 0.2, y: topY + 0.38, w: topW - 0.4, h: 0.02,
    fill: { color: colors.steel }
});

// 5个子项
const supW = 0.78;
const supGap = 0.1;
const supStartX = 2.95;

const supplies = ["港务工程公司", "修造船厂", "燃料公司", "水电公司", "其他配套"];
supplies.forEach((item, i) => {
    const x = supStartX + i * (supW + supGap);
    slide.addShape(pres.shapes.RECTANGLE, {
        x: x, y: topY + 0.48, w: supW, h: 0.32,
        fill: { color: colors.steel }
    });
    slide.addText(item, {
        x: x, y: topY + 0.48, w: supW, h: 0.32,
        fontSize: 9, bold: true,
        color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 向下双箭头
slide.addShape(pres.shapes.LINE, {
    x: 4.7, y: 1.88, w: 0, h: 0.4,
    line: { color: colors.line, width: 2.5, arrowEnd: { type: 'triangle', size: 8 } }
});
slide.addShape(pres.shapes.LINE, {
    x: 5.3, y: 1.88, w: 0, h: 0.4,
    line: { color: colors.line, width: 2.5, arrowEnd: { type: 'triangle', size: 8 } }
});

// ========== 中间主体 ==========
const mainY = 2.35;
const mainH = 3.2;
const mainX = 1.2;
const mainW = 6.8;

// 供应商椭圆
slide.addShape(pres.shapes.OVAL, {
    x: 0.15, y: mainY + 0.9, w: 1.0, h: 1.4,
    fill: { color: colors.white },
    line: { color: colors.gold, width: 3 }
});
slide.addText("供应商", {
    x: 0.15, y: mainY + 0.9, w: 1.0, h: 1.4,
    fontSize: 16, bold: true,
    color: colors.gold, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 1.2, y: mainY + 1.5, w: 0.25, h: 0,
    line: { color: colors.line, width: 2.5, arrowEnd: { type: 'triangle', size: 7 } }
});
slide.addShape(pres.shapes.LINE, {
    x: 1.2, y: mainY + 1.75, w: 0.25, h: 0,
    line: { color: colors.line, width: 2.5, arrowBegin: { type: 'triangle', size: 7 } }
});

// 港口物流主框
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX, y: mainY, w: mainW, h: mainH,
    fill: { color: colors.white },
    line: { color: colors.navy, width: 3 }
});

// 竖向标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: mainX + 0.15, y: mainY + 0.7, w: 0.45, h: 1.8,
    fill: { color: colors.navy }
});
slide.addText("港\n口\n物\n流\n服\n务\n商", {
    x: mainX + 0.15, y: mainY + 0.7, w: 0.45, h: 1.8,
    fontSize: 13, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 左侧服务项
const svcX = mainX + 0.7;
const svcW = 2.6;
const svcH = 0.36;
const rowH = 0.42;

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
    const y = mainY + 0.2 + svc.y * rowH;
    
    slide.addShape(pres.shapes.RECTANGLE, {
        x: svcX, y: y, w: svcW, h: svcH,
        fill: { color: colors.slate }
    });
    slide.addText(svc.name, {
        x: svcX, y: y, w: svcW, h: svcH,
        fontSize: 10, bold: true,
        color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
    
    if (svc.arrow) {
        slide.addShape(pres.shapes.LINE, {
            x: svcX + svcW + 0.1, y: y + svcH/2, w: 0.5, h: 0,
            line: { color: colors.line, width: 2, arrowEnd: { type: 'triangle', size: 6 } }
        });
    }
});

// 右侧连接框
const rightX = mainX + 3.9;

// 包装分拣
slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: mainY + 0.2 + 2 * rowH, w: 2.6, h: 0.36,
    fill: { color: colors.silver }
});
slide.addText("包装、分拣流通加工公司", {
    x: rightX, y: mainY + 0.2 + 2 * rowH, w: 2.6, h: 0.36,
    fontSize: 10, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 货代多式联运
slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: mainY + 0.2 + 3 * rowH, w: 2.6, h: 0.75,
    fill: { color: colors.silver }
});
slide.addText("货代、船代、中转公司\n海、陆、空多式联运", {
    x: rightX, y: mainY + 0.2 + 3 * rowH, w: 2.6, h: 0.75,
    fontSize: 9, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 保税仓储
slide.addShape(pres.shapes.RECTANGLE, {
    x: rightX, y: mainY + 0.2 + 5 * rowH, w: 2.6, h: 0.36,
    fill: { color: colors.silver }
});
slide.addText("保税与非保税仓储公司", {
    x: rightX, y: mainY + 0.2 + 5 * rowH, w: 2.6, h: 0.36,
    fontSize: 10, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 向右箭头
slide.addShape(pres.shapes.LINE, {
    x: mainX + mainW + 0.1, y: mainY + 1.5, w: 0.3, h: 0,
    line: { color: colors.line, width: 2.5, arrowEnd: { type: 'triangle', size: 7 } }
});

// 销售商
slide.addShape(pres.shapes.RECTANGLE, {
    x: 8.15, y: mainY + 1.1, w: 0.9, h: 0.9,
    fill: { color: colors.white },
    line: { color: colors.gold, width: 3 }
});
slide.addText("销售商", {
    x: 8.15, y: mainY + 1.1, w: 0.9, h: 0.9,
    fontSize: 14, bold: true,
    color: colors.gold, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 销售商双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 9.1, y: mainY + 1.45, w: 0.3, h: 0,
    line: { color: colors.line, width: 2.5, arrowEnd: { type: 'triangle', size: 7 } }
});
slide.addShape(pres.shapes.LINE, {
    x: 9.1, y: mainY + 1.7, w: 0.3, h: 0,
    line: { color: colors.line, width: 2.5, arrowBegin: { type: 'triangle', size: 7 } }
});

// 客户
slide.addShape(pres.shapes.OVAL, {
    x: 9.5, y: mainY + 0.8, w: 1.0, h: 1.4,
    fill: { color: colors.white },
    line: { color: colors.navy, width: 3 }
});
slide.addText("客户/\n需求源", {
    x: 9.5, y: mainY + 0.8, w: 1.0, h: 1.4,
    fontSize: 13, bold: true,
    color: colors.navy, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// ========== 底部：配套服务提供商 ==========
// 向上双箭头
slide.addShape(pres.shapes.LINE, {
    x: 4.7, y: mainY + mainH + 0.05, w: 0, h: 0.4,
    line: { color: colors.line, width: 2.5, arrowEnd: { type: 'triangle', size: 8 } }
});
slide.addShape(pres.shapes.LINE, {
    x: 5.3, y: mainY + mainH + 0.05, w: 0, h: 0.4,
    line: { color: colors.line, width: 2.5, arrowEnd: { type: 'triangle', size: 8 } }
});

const bottomY = mainY + mainH + 0.5;

slide.addShape(pres.shapes.RECTANGLE, {
    x: topX, y: bottomY, w: topW, h: 0.9,
    fill: { color: colors.white },
    line: { color: colors.steel, width: 2 }
});
slide.addText("配套服务提供商", {
    x: topX, y: bottomY + 0.08, w: topW, h: 0.3,
    fontSize: 14, bold: true,
    color: colors.navy, align: "center", fontFace: "Microsoft YaHei"
});

// 分隔线
slide.addShape(pres.shapes.RECTANGLE, {
    x: topX + 0.2, y: bottomY + 0.38, w: topW - 0.4, h: 0.02,
    fill: { color: colors.steel }
});

// 5个子项
const supportServices = ["设计研究所", "银行保险", "劳务公司", "教育培训", "其他服务"];
supportServices.forEach((item, i) => {
    const x = supStartX + i * (supW + supGap);
    slide.addShape(pres.shapes.RECTANGLE, {
        x: x, y: bottomY + 0.48, w: supW, h: 0.32,
        fill: { color: colors.steel }
    });
    slide.addText(item, {
        x: x, y: bottomY + 0.48, w: supW, h: 0.32,
        fontSize: 9, bold: true,
        color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 保存
pres.writeFile({ fileName: "/root/.openclaw/workspace/港口物流服务供应链.pptx" });
console.log("PPT 已保存: /root/.openclaw/workspace/港口物流服务供应链.pptx");

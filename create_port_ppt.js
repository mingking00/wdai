const pptxgen = require("pptxgenjs");

// 创建演示文稿
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = "港口物流服务供应链";
pres.author = "wdai";

// 颜色定义
const colors = {
    primary: "B58900",      // 金色 - 供应商/销售商
    secondary: "2C3E50",    // 深蓝 - 港口物流
    accent: "5D737E",       // 灰蓝 - 配套服务
    bg: "F8F9FA",          // 浅灰背景
    white: "FFFFFF",
    textDark: "2C3E50"
};

// 添加第一页 - 港口物流服务供应链
let slide1 = pres.addSlide();
slide1.background = { color: colors.bg };

// 标题
slide1.addText("港口物流服务供应链", {
    x: 0, y: 0.2, w: 10, h: 0.6,
    fontSize: 28, fontFace: "Microsoft YaHei", bold: true,
    color: colors.textDark, align: "center"
});

// 分隔线
slide1.addShape(pres.shapes.RECTANGLE, {
    x: 4.2, y: 0.85, w: 1.6, h: 0.05,
    fill: { color: colors.primary }
});

// ========== 供应商（顶部）==========
slide1.addShape(pres.shapes.OVAL, {
    x: 4, y: 1.0, w: 2, h: 0.5,
    fill: { color: colors.primary }
});
slide1.addText("供应商", {
    x: 4, y: 1.0, w: 2, h: 0.5,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true,
    color: colors.white, align: "center", valign: "middle"
});

// 箭头：供应商 → 港口物流
slide1.addShape(pres.shapes.LINE, {
    x: 5, y: 1.5, w: 0, h: 0.4,
    line: { color: colors.accent, width: 2, arrowEnd: { type: 'triangle', size: 8 } }
});

// ========== 主体区域 ==========
const mainY = 2.1;
const mainH = 3.0;

// 左侧：配套服务提供商
slide1.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: mainY, w: 1.5, h: mainH,
    fill: { color: colors.white },
    line: { color: colors.textDark, width: 2 }
});
slide1.addText("配套服务提供商", {
    x: 0.3, y: mainY + 0.1, w: 1.5, h: 0.4,
    fontSize: 11, fontFace: "Microsoft YaHei", bold: true,
    color: colors.textDark, align: "center", valign: "middle"
});
// 分隔线
slide1.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: mainY + 0.5, w: 1.3, h: 0.03,
    fill: { color: colors.textDark }
});

// 配套服务列表
const services = ["设计研究所", "银行保险", "劳务公司", "教育培训", "其他服务"];
services.forEach((service, i) => {
    slide1.addShape(pres.shapes.RECTANGLE, {
        x: 0.45, y: mainY + 0.65 + i * 0.45, w: 1.2, h: 0.35,
        fill: { color: colors.accent }
    });
    slide1.addText(service, {
        x: 0.45, y: mainY + 0.65 + i * 0.45, w: 1.2, h: 0.35,
        fontSize: 9, fontFace: "Microsoft YaHei",
        color: colors.white, align: "center", valign: "middle"
    });
});

// 左箭头：配套服务 → 港口物流
slide1.addShape(pres.shapes.LINE, {
    x: 1.85, y: mainY + mainH/2 - 0.05, w: 0.5, h: 0,
    line: { color: colors.accent, width: 2, arrowEnd: { type: 'triangle', size: 6 } }
});

// 中间：港口物流服务提供商
slide1.addShape(pres.shapes.RECTANGLE, {
    x: 2.4, y: mainY, w: 5.2, h: mainH,
    fill: { color: colors.white },
    line: { color: colors.textDark, width: 2 }
});
slide1.addText("港口物流服务提供商", {
    x: 2.4, y: mainY + 0.1, w: 5.2, h: 0.4,
    fontSize: 13, fontFace: "Microsoft YaHei", bold: true,
    color: colors.textDark, align: "center", valign: "middle"
});
// 分隔线
slide1.addShape(pres.shapes.RECTANGLE, {
    x: 2.5, y: mainY + 0.5, w: 5, h: 0.03,
    fill: { color: colors.textDark }
});

// 港口物流服务网格
const logisticsServices = [
    ["引航服务提供商\n拖轮公司", "理货服务提供商\n理货公司", "配送服务提供商", "运输服务提供商"],
    ["装卸服务提供商\n装卸公司", "仓储服务提供商", "关检服务机构\n一关三检", ""],
    ["货代、船代、\n中转公司", "海、陆、空\n多式联运公司", "保税与非保税\n仓储公司", ""],
    ["包装、分拣\n流通加工公司", "", "", ""]
];

const boxW = 1.15;
const boxH = 0.55;
const gapX = 0.15;
const startX = 2.55;
const startY = mainY + 0.65;

logisticsServices.forEach((row, rowIdx) => {
    row.forEach((service, colIdx) => {
        if (service) {
            const x = startX + colIdx * (boxW + gapX);
            const y = startY + rowIdx * (boxH + 0.05);
            
            slide1.addShape(pres.shapes.RECTANGLE, {
                x: x, y: y, w: boxW, h: boxH,
                fill: { color: colors.secondary }
            });
            slide1.addText(service, {
                x: x, y: y, w: boxW, h: boxH,
                fontSize: 7, fontFace: "Microsoft YaHei",
                color: colors.white, align: "center", valign: "middle"
            });
        }
    });
});

// 右箭头：物流配给 → 港口物流
slide1.addShape(pres.shapes.LINE, {
    x: 7.65, y: mainY + mainH/2 - 0.05, w: 0.5, h: 0,
    line: { color: colors.accent, width: 2, arrowBegin: { type: 'triangle', size: 6 } }
});

// 右侧：物流配给供应商
slide1.addShape(pres.shapes.RECTANGLE, {
    x: 8.1, y: mainY, w: 1.5, h: mainH,
    fill: { color: colors.white },
    line: { color: colors.textDark, width: 2 }
});
slide1.addText("物流配给供应商", {
    x: 8.1, y: mainY + 0.1, w: 1.5, h: 0.4,
    fontSize: 11, fontFace: "Microsoft YaHei", bold: true,
    color: colors.textDark, align: "center", valign: "middle"
});
// 分隔线
slide1.addShape(pres.shapes.RECTANGLE, {
    x: 8.2, y: mainY + 0.5, w: 1.3, h: 0.03,
    fill: { color: colors.textDark }
});

// 物流配给列表
const supplies = ["港务工程公司", "修造船厂", "燃料公司", "水电公司", "其他配套"];
supplies.forEach((supply, i) => {
    slide1.addShape(pres.shapes.RECTANGLE, {
        x: 8.25, y: mainY + 0.65 + i * 0.45, w: 1.2, h: 0.35,
        fill: { color: colors.accent }
    });
    slide1.addText(supply, {
        x: 8.25, y: mainY + 0.65 + i * 0.45, w: 1.2, h: 0.35,
        fontSize: 9, fontFace: "Microsoft YaHei",
        color: colors.white, align: "center", valign: "middle"
    });
});

// ========== 底部：销售商 → 客户 ==========
// 箭头：港口物流 → 销售商
slide1.addShape(pres.shapes.LINE, {
    x: 5, y: mainY + mainH + 0.1, w: 0, h: 0.35,
    line: { color: colors.accent, width: 2, arrowEnd: { type: 'triangle', size: 8 } }
});

// 销售商
const sellerY = mainY + mainH + 0.55;
slide1.addShape(pres.shapes.OVAL, {
    x: 4, y: sellerY, w: 2, h: 0.5,
    fill: { color: colors.primary }
});
slide1.addText("销售商", {
    x: 4, y: sellerY, w: 2, h: 0.5,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true,
    color: colors.white, align: "center", valign: "middle"
});

// 箭头：销售商 → 客户
slide1.addShape(pres.shapes.LINE, {
    x: 5, y: sellerY + 0.55, w: 0, h: 0.35,
    line: { color: colors.accent, width: 2, arrowEnd: { type: 'triangle', size: 8 } }
});

// 客户/需求源
const customerY = sellerY + 1.0;
slide1.addShape(pres.shapes.OVAL, {
    x: 4, y: customerY, w: 2, h: 0.5,
    fill: { color: colors.secondary }
});
slide1.addText("客户 / 需求源", {
    x: 4, y: customerY, w: 2, h: 0.5,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true,
    color: colors.white, align: "center", valign: "middle"
});

// 保存文件
pres.writeFile({ fileName: "/root/.openclaw/workspace/港口物流服务供应链.pptx" });
console.log("PPT 已保存到: /root/.openclaw/workspace/港口物流服务供应链.pptx");

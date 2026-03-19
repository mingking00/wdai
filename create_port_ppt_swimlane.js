const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = "港口物流服务供应链";

// 专业配色 - 分区明确
const colors = {
    // 供应商区 - 暖色调
    supplierBg: "FFF7ED",
    supplierMain: "EA580C",
    supplierLight: "FED7AA",
    
    // 港口物流区 - 主色调（深蓝）
    portBg: "EFF6FF",
    portMain: "1E40AF",
    portLight: "BFDBFE",
    
    // 客户区 - 绿色调
    customerBg: "F0FDF4",
    customerMain: "166534",
    customerLight: "BBF7D0",
    
    // 通用
    white: "FFFFFF",
    textDark: "1F2937",
    textLight: "6B7280",
    border: "E5E7EB",
    arrow: "4B5563"
};

// ===== 第1页：全景图（泳道设计） =====
let slide = pres.addSlide();
slide.background = { color: "F9FAFB" };

// 标题
slide.addText("港口物流服务供应链全景图", {
    x: 0, y: 0.2, w: 10, h: 0.6,
    fontSize: 28, bold: true,
    color: colors.textDark, align: "center", fontFace: "Microsoft YaHei"
});

// === 泳道1：上游供应商（顶部）===
// 背景色块
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.0, w: 9.4, h: 1.1,
    fill: { color: colors.supplierBg }
});

// 标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.0, w: 1.5, h: 1.1,
    fill: { color: colors.supplierMain }
});
slide.addText("上游\n供应商", {
    x: 0.3, y: 1.0, w: 1.5, h: 1.1,
    fontSize: 14, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 物流配给供应商
slide.addShape(pres.shapes.RECTANGLE, {
    x: 2.0, y: 1.1, w: 2.0, h: 0.4,
    fill: { color: colors.white },
    line: { color: colors.supplierMain, width: 2 }
});
slide.addText("物流配给供应商", {
    x: 2.0, y: 1.1, w: 2.0, h: 0.4,
    fontSize: 11, bold: true,
    color: colors.supplierMain, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 5个子项
const supItems = ["港务工程", "修造船厂", "燃料公司", "水电", "其他"];
supItems.forEach((item, i) => {
    slide.addShape(pres.shapes.RECTANGLE, {
        x: 2.0 + i * 0.55, y: 1.6, w: 0.5, h: 0.35,
        fill: { color: colors.supplierLight }
    });
    slide.addText(item, {
        x: 2.0 + i * 0.55, y: 1.6, w: 0.5, h: 0.35,
        fontSize: 7, bold: true,
        color: colors.textDark, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 配套服务
slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.8, y: 1.1, w: 2.0, h: 0.4,
    fill: { color: colors.white },
    line: { color: colors.supplierMain, width: 2 }
});
slide.addText("配套服务提供商", {
    x: 5.8, y: 1.1, w: 2.0, h: 0.4,
    fontSize: 11, bold: true,
    color: colors.supplierMain, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

const supportItems = ["设计所", "银行保险", "劳务", "培训", "其他"];
supportItems.forEach((item, i) => {
    slide.addShape(pres.shapes.RECTANGLE, {
        x: 5.8 + i * 0.55, y: 1.6, w: 0.5, h: 0.35,
        fill: { color: colors.supplierLight }
    });
    slide.addText(item, {
        x: 5.8 + i * 0.55, y: 1.6, w: 0.5, h: 0.35,
        fontSize: 7, bold: true,
        color: colors.textDark, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 向下箭头
slide.addShape(pres.shapes.LINE, {
    x: 3.9, y: 2.15, w: 0, h: 0.3,
    line: { color: colors.arrow, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});
slide.addShape(pres.shapes.LINE, {
    x: 6.7, y: 2.15, w: 0, h: 0.3,
    line: { color: colors.arrow, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});

// === 泳道2：港口物流核心区（中间）===
// 背景色块
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 2.5, w: 9.4, h: 2.4,
    fill: { color: colors.portBg }
});

// 标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 2.5, w: 1.5, h: 2.4,
    fill: { color: colors.portMain }
});
slide.addText("港口物流\n服务商", {
    x: 0.3, y: 2.5, w: 1.5, h: 2.4,
    fontSize: 14, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 左侧：供应商连接
slide.addShape(pres.shapes.OVAL, {
    x: 2.0, y: 3.3, w: 0.9, h: 0.7,
    fill: { color: colors.white },
    line: { color: colors.supplierMain, width: 2 }
});
slide.addText("供应商", {
    x: 2.0, y: 3.3, w: 0.9, h: 0.7,
    fontSize: 10, bold: true,
    color: colors.supplierMain, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 2.95, y: 3.55, w: 0.3, h: 0,
    line: { color: colors.arrow, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
});
slide.addShape(pres.shapes.LINE, {
    x: 2.95, y: 3.75, w: 0.3, h: 0,
    line: { color: colors.arrow, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 5 }
});

// 核心服务卡片 - 使用网格布局
const services = [
    { name: "引航服务", sub: "拖轮公司", x: 3.4, y: 2.7 },
    { name: "理货服务", sub: "理货公司", x: 5.0, y: 2.7 },
    { name: "配送服务", sub: "最后一公里", x: 6.6, y: 2.7 },
    { name: "运输服务", sub: "多式联运", x: 3.4, y: 3.5 },
    { name: "装卸服务", sub: "装卸公司", x: 5.0, y: 3.5 },
    { name: "仓储服务", sub: "保税/非保税", x: 6.6, y: 3.5 },
    { name: "关检服务", sub: "一关三检", x: 4.3, y: 4.3 },
    { name: "货代服务", sub: "船代/中转", x: 5.7, y: 4.3 }
];

services.forEach(svc => {
    slide.addShape(pres.shapes.RECTANGLE, {
        x: svc.x, y: svc.y, w: 1.4, h: 0.65,
        fill: { color: colors.white },
        line: { color: colors.portMain, width: 1.5 }
    });
    slide.addText(svc.name, {
        x: svc.x, y: svc.y + 0.08, w: 1.4, h: 0.28,
        fontSize: 10, bold: true,
        color: colors.portMain, align: "center", fontFace: "Microsoft YaHei"
    });
    slide.addText(svc.sub, {
        x: svc.x, y: svc.y + 0.36, w: 1.4, h: 0.22,
        fontSize: 7,
        color: colors.textLight, align: "center", fontFace: "Microsoft YaHei"
    });
});

// 右侧扩展服务
const extServices = [
    { name: "包装分拣", y: 2.7 },
    { name: "流通加工", y: 3.5 },
    { name: "多式联运", y: 4.3 }
];
extServices.forEach(ext => {
    slide.addShape(pres.shapes.RECTANGLE, {
        x: 8.2, y: ext.y, w: 1.2, h: 0.5,
        fill: { color: colors.portLight }
    });
    slide.addText(ext.name, {
        x: 8.2, y: ext.y, w: 1.2, h: 0.5,
        fontSize: 8, bold: true,
        color: colors.portMain, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
    // 连接线
    slide.addShape(pres.shapes.LINE, {
        x: 8.0, y: ext.y + 0.25, w: 0.18, h: 0,
        line: { color: colors.arrow, width: 1.5, arrowTypeEnd: 'triangle', arrowSizeEnd: 4 }
    });
});

// 向右到销售商的箭头
slide.addShape(pres.shapes.LINE, {
    x: 8.0, y: 3.15, w: 0.4, h: 0,
    line: { color: colors.arrow, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});

// === 泳道3：下游客户（底部）===
// 背景色块
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 5.0, w: 9.4, h: 0.5,
    fill: { color: colors.customerBg }
});

// 标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 5.0, w: 1.5, h: 0.5,
    fill: { color: colors.customerMain }
});
slide.addText("下游客户", {
    x: 0.3, y: 5.0, w: 1.5, h: 0.5,
    fontSize: 12, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 销售商
slide.addShape(pres.shapes.RECTANGLE, {
    x: 2.5, y: 5.1, w: 1.2, h: 0.3,
    fill: { color: colors.white },
    line: { color: colors.customerMain, width: 2 }
});
slide.addText("销售商", {
    x: 2.5, y: 5.1, w: 1.2, h: 0.3,
    fontSize: 10, bold: true,
    color: colors.customerMain, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 双向箭头到客户
slide.addShape(pres.shapes.LINE, {
    x: 3.75, y: 5.2, w: 0.25, h: 0,
    line: { color: colors.arrow, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
});
slide.addShape(pres.shapes.LINE, {
    x: 3.75, y: 5.35, w: 0.25, h: 0,
    line: { color: colors.arrow, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 5 }
});

// 客户
slide.addShape(pres.shapes.OVAL, {
    x: 4.1, y: 5.05, w: 1.0, h: 0.4,
    fill: { color: colors.white },
    line: { color: colors.customerMain, width: 2 }
});
slide.addText("客户/需求源", {
    x: 4.1, y: 5.05, w: 1.0, h: 0.4,
    fontSize: 9, bold: true,
    color: colors.customerMain, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 图例
slide.addText("■ 供应商", { x: 6.5, y: 5.15, w: 1, h: 0.25, fontSize: 8, color: colors.supplierMain, fontFace: "Microsoft YaHei" });
slide.addText("■ 港口物流", { x: 7.5, y: 5.15, w: 1, h: 0.25, fontSize: 8, color: colors.portMain, fontFace: "Microsoft YaHei" });
slide.addText("■ 客户", { x: 8.5, y: 5.15, w: 0.8, h: 0.25, fontSize: 8, color: colors.customerMain, fontFace: "Microsoft YaHei" });

// 保存
const outputPath = "/root/.openclaw/workspace/港口物流服务供应链_泳道版.pptx";
pres.writeFile({ fileName: outputPath });
console.log("泳道版PPT已保存: " + outputPath);

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = "港口物流服务供应链";

// 配色方案 - 参考第二张图的分区颜色
const colors = {
    // 上游供应商 - 橙色
    upstream: "EA580C",
    upstreamLight: "FFF7ED",
    upstreamText: "C2410C",
    
    // 核心港口物流 - 蓝色
    core: "1D4ED8",
    coreLight: "EFF6FF",
    coreText: "1E40AF",
    
    // 下游客户 - 绿色
    downstream: "15803D",
    downstreamLight: "F0FDF4",
    downstreamText: "166534",
    
    // 通用
    white: "FFFFFF",
    text: "1F2937",
    textLight: "6B7280",
    line: "9CA3AF"
};

// ===== 主页面 =====
const slide = pres.addSlide();
slide.background = { color: "FAFAFA" };

// 标题
slide.addText("港口物流服务供应链", {
    x: 0, y: 0.2, w: 10, h: 0.6,
    fontSize: 28, bold: true,
    color: colors.text, align: "center", fontFace: "Microsoft YaHei"
});

// ===== 第1区：上游供应商（顶部橙色区）=====
// 上游供应商大标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.9, w: 1.8, h: 1.0,
    fill: { color: colors.upstream }
});
slide.addText("上游供应商", {
    x: 0.5, y: 0.9, w: 1.8, h: 1.0,
    fontSize: 16, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 物流配给供应商框
slide.addShape(pres.shapes.RECTANGLE, {
    x: 2.5, y: 0.9, w: 6.0, h: 0.5,
    fill: { color: colors.upstreamLight },
    line: { color: colors.upstream, width: 2 }
});
slide.addText("物流配给供应商", {
    x: 2.5, y: 0.9, w: 6.0, h: 0.5,
    fontSize: 13, bold: true,
    color: colors.upstreamText, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 5个子项
const topItems = ["港务工程", "修造船厂", "燃料公司", "水电公司", "其他配套"];
topItems.forEach((item, i) => {
    slide.addShape(pres.shapes.RECTANGLE, {
        x: 2.5 + i * 1.2, y: 1.5, w: 1.1, h: 0.4,
        fill: { color: colors.upstreamLight },
        line: { color: colors.upstream, width: 1 }
    });
    slide.addText(item, {
        x: 2.5 + i * 1.2, y: 1.5, w: 1.1, h: 0.4,
        fontSize: 9, bold: true,
        color: colors.upstreamText, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 向下箭头
slide.addShape(pres.shapes.LINE, {
    x: 5.5, y: 2.0, w: 0, h: 0.4,
    line: { color: colors.text, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 6 }
});

// ===== 第2区：港口物流服务商（中间蓝色区）=====
// 大标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.5, w: 1.8, h: 3.0,
    fill: { color: colors.core }
});
slide.addText("港口物流\n服务商", {
    x: 0.5, y: 2.5, w: 1.8, h: 3.0,
    fontSize: 16, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 核心区域背景
slide.addShape(pres.shapes.RECTANGLE, {
    x: 2.5, y: 2.5, w: 7.0, h: 3.0,
    fill: { color: colors.coreLight },
    line: { color: colors.core, width: 2 }
});

// 左侧供应商椭圆
slide.addShape(pres.shapes.OVAL, {
    x: 2.7, y: 3.8, w: 1.0, h: 0.8,
    fill: { color: colors.upstreamLight },
    line: { color: colors.upstream, width: 2 }
});
slide.addText("供应商", {
    x: 2.7, y: 3.8, w: 1.0, h: 0.8,
    fontSize: 11, bold: true,
    color: colors.upstreamText, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 双向箭头（左侧）
slide.addShape(pres.shapes.LINE, {
    x: 3.75, y: 4.1, w: 0.3, h: 0,
    line: { color: colors.upstream, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
});
slide.addShape(pres.shapes.LINE, {
    x: 3.75, y: 4.3, w: 0.3, h: 0,
    line: { color: colors.upstream, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 5 }
});

// 7项服务列表
const services = [
    { name: "引航服务", sub: "拖轮公司", y: 2.7, hasRight: false },
    { name: "理货服务", sub: "理货公司", y: 3.2, hasRight: false },
    { name: "配送服务", sub: "配送服务提供商", y: 3.7, hasRight: true, rightText: "包装、分拣\n流通加工公司" },
    { name: "运输服务", sub: "运输服务提供商", y: 4.2, hasRight: true, rightText: "货代、船代、中转\n海陆空联运公司" },
    { name: "装卸服务", sub: "装卸公司", y: 4.7, hasRight: false },
    { name: "仓储服务", sub: "仓储服务提供商", y: 5.2, hasRight: true, rightText: "保税与非保税\n仓储公司" },
    { name: "关检服务", sub: "一关三检", y: 5.7, hasRight: false }
];

services.forEach(svc => {
    // 主服务卡片
    slide.addShape(pres.shapes.RECTANGLE, {
        x: 4.2, y: svc.y, w: 2.2, h: 0.45,
        fill: { color: colors.white },
        line: { color: colors.core, width: 1.5 }
    });
    slide.addText(svc.name, {
        x: 4.2, y: svc.y + 0.02, w: 2.2, h: 0.25,
        fontSize: 11, bold: true,
        color: colors.coreText, align: "center", fontFace: "Microsoft YaHei"
    });
    slide.addText(svc.sub, {
        x: 4.2, y: svc.y + 0.27, w: 2.2, h: 0.16,
        fontSize: 7,
        color: colors.textLight, align: "center", fontFace: "Microsoft YaHei"
    });
    
    // 向右延伸
    if (svc.hasRight) {
        // 连接线
        slide.addShape(pres.shapes.LINE, {
            x: 6.45, y: svc.y + 0.22, w: 0.4, h: 0,
            line: { color: colors.core, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
        });
        
        // 延伸卡片
        slide.addShape(pres.shapes.RECTANGLE, {
            x: 6.9, y: svc.y - 0.05, w: 2.0, h: 0.55,
            fill: { color: "DBEAFE" },
            line: { color: colors.core, width: 1.5 }
        });
        slide.addText(svc.rightText, {
            x: 6.9, y: svc.y - 0.05, w: 2.0, h: 0.55,
            fontSize: 8,
            color: colors.text, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
        });
    }
});

// 右侧销售商
slide.addShape(pres.shapes.RECTANGLE, {
    x: 8.2, y: 4.0, w: 0.9, h: 0.5,
    fill: { color: colors.downstreamLight },
    line: { color: colors.downstream, width: 2 }
});
slide.addText("销售商", {
    x: 8.2, y: 4.0, w: 0.9, h: 0.5,
    fontSize: 11, bold: true,
    color: colors.downstreamText, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 销售商到客户的双向箭头
slide.addShape(pres.shapes.LINE, {
    x: 9.15, y: 4.2, w: 0.3, h: 0,
    line: { color: colors.downstream, width: 2, arrowTypeEnd: 'triangle', arrowSizeEnd: 5 }
});
slide.addShape(pres.shapes.LINE, {
    x: 9.15, y: 4.35, w: 0.3, h: 0,
    line: { color: colors.downstream, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 5 }
});

// 客户椭圆
slide.addShape(pres.shapes.OVAL, {
    x: 9.5, y: 3.8, w: 0.9, h: 0.9,
    fill: { color: colors.downstreamLight },
    line: { color: colors.downstream, width: 2 }
});
slide.addText("客户", {
    x: 9.5, y: 3.85, w: 0.9, h: 0.5,
    fontSize: 11, bold: true,
    color: colors.downstreamText, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});
slide.addText("需求源", {
    x: 9.5, y: 4.3, w: 0.9, h: 0.3,
    fontSize: 8,
    color: colors.downstreamText, align: "center", fontFace: "Microsoft YaHei"
});

// ===== 第3区：下游客户（底部绿色区）=====
// 大标签
slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.7, w: 1.8, h: 1.0,
    fill: { color: colors.downstream }
});
slide.addText("下游客户", {
    x: 0.5, y: 5.7, w: 1.8, h: 1.0,
    fontSize: 16, bold: true,
    color: colors.white, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 配套服务区域
slide.addShape(pres.shapes.RECTANGLE, {
    x: 2.5, y: 5.7, w: 6.0, h: 0.5,
    fill: { color: colors.downstreamLight },
    line: { color: colors.downstream, width: 2 }
});
slide.addText("配套服务提供商", {
    x: 2.5, y: 5.7, w: 6.0, h: 0.5,
    fontSize: 13, bold: true,
    color: colors.downstreamText, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 5个子项
const bottomItems = ["设计研究所", "银行保险", "劳务公司", "教育培训", "其他服务"];
bottomItems.forEach((item, i) => {
    slide.addShape(pres.shapes.RECTANGLE, {
        x: 2.5 + i * 1.2, y: 6.3, w: 1.1, h: 0.4,
        fill: { color: colors.downstreamLight },
        line: { color: colors.downstream, width: 1 }
    });
    slide.addText(item, {
        x: 2.5 + i * 1.2, y: 6.3, w: 1.1, h: 0.4,
        fontSize: 9, bold: true,
        color: colors.downstreamText, align: "center", valign: "middle", fontFace: "Microsoft YaHei"
    });
});

// 向上箭头
slide.addShape(pres.shapes.LINE, {
    x: 5.5, y: 5.5, w: 0, h: 0.15,
    line: { color: colors.downstream, width: 2, arrowTypeBegin: 'triangle', arrowSizeBegin: 6 }
});

// 保存
const outputPath = "/root/.openclaw/workspace/港口物流服务供应链_分区版.pptx";
pres.writeFile({ fileName: outputPath });
console.log("分区版PPT已保存: " + outputPath);

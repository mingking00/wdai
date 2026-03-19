const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.author = 'Kimi Claw';
pres.title = '现代港口物流的形成';

// 配色方案 - Ocean Gradient (港口主题)
const colors = {
  primary: "065A82",    // 深蓝
  secondary: "1C7293",  // 蓝绿
  accent: "21295C",     // 午夜蓝
  light: "F0F4F8",      // 浅灰蓝
  white: "FFFFFF",
  text: "1A202C"
};

// ========== 标题页 ==========
let titleSlide = pres.addSlide();
titleSlide.background = { color: colors.primary };

titleSlide.addText("现代港口物流的形成", {
  x: 1, y: 2, w: 8, h: 1.5,
  fontSize: 44, fontFace: "Arial Black", color: colors.white,
  align: "center", valign: "middle"
});

titleSlide.addText("Formation of Modern Port Logistics", {
  x: 1, y: 3.5, w: 8, h: 0.8,
  fontSize: 18, fontFace: "Arial", color: "93C5FD",
  align: "center", valign: "middle", italic: true
});

titleSlide.addText("从传统运输到全球供应链的演进历程", {
  x: 1, y: 4.5, w: 8, h: 0.6,
  fontSize: 16, fontFace: "Arial", color: colors.white,
  align: "center", valign: "middle"
});

// 装饰线条
titleSlide.addShape(pres.shapes.RECTANGLE, {
  x: 3.5, y: 4.2, w: 3, h: 0.05, fill: { color: "93C5FD" }
});

// ========== 目录页 ==========
let tocSlide = pres.addSlide();
tocSlide.background = { color: colors.light };

tocSlide.addText("内容大纲", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 32, fontFace: "Arial Black", color: colors.primary,
  align: "left", valign: "middle"
});

const tocItems = [
  { num: "01", title: "发展的四个阶段", desc: "从传统物流到供应链物流的演进" },
  { num: "02", title: "传统物流阶段", desc: "20世纪40年代 - 基础运输功能" },
  { num: "03", title: "配送物流阶段", desc: "20世纪60-80年代 - 技术革新" },
  { num: "04", title: "综合物流阶段", desc: "20世纪80-90年代 - 信息化发展" },
  { num: "05", title: "供应链物流阶段", desc: "21世纪至今 - 全球化整合" }
];

let yPos = 1.5;
tocItems.forEach((item, index) => {
  // 编号圆圈
  tocSlide.addShape(pres.shapes.OVAL, {
    x: 0.8, y: yPos, w: 0.6, h: 0.6,
    fill: { color: index === 0 ? colors.primary : colors.secondary }
  });
  
  tocSlide.addText(item.num, {
    x: 0.8, y: yPos, w: 0.6, h: 0.6,
    fontSize: 14, fontFace: "Arial Black", color: colors.white,
    align: "center", valign: "middle"
  });
  
  // 标题
  tocSlide.addText(item.title, {
    x: 1.7, y: yPos + 0.05, w: 7, h: 0.4,
    fontSize: 18, fontFace: "Arial", color: colors.text, bold: true
  });
  
  // 描述
  tocSlide.addText(item.desc, {
    x: 1.7, y: yPos + 0.45, w: 7, h: 0.3,
    fontSize: 12, fontFace: "Arial", color: "64748B"
  });
  
  yPos += 0.9;
});

// ========== 四个阶段总览 ==========
let overviewSlide = pres.addSlide();
overviewSlide.background = { color: colors.white };

overviewSlide.addText("港口物流发展的四个阶段", {
  x: 0.5, y: 0.4, w: 9, h: 0.8,
  fontSize: 32, fontFace: "Arial Black", color: colors.primary
});

// 时间线
const stages = [
  { period: "1940s+", title: "传统物流", color: "94A3B8" },
  { period: "1960-80s", title: "配送物流", color: "60A5FA" },
  { period: "1980-90s", title: "综合物流", color: "3B82F6" },
  { period: "2000s+", title: "供应链物流", color: colors.primary }
];

// 时间线主轴
overviewSlide.addShape(pres.shapes.RECTANGLE, {
  x: 0.8, y: 2.5, w: 8.4, h: 0.08, fill: { color: colors.secondary }
});

// 四个节点
let xPos = 1.2;
stages.forEach((stage, index) => {
  // 节点圆
  overviewSlide.addShape(pres.shapes.OVAL, {
    x: xPos, y: 2.35, w: 0.4, h: 0.4,
    fill: { color: stage.color }
  });
  
  // 时期
  overviewSlide.addText(stage.period, {
    x: xPos - 0.3, y: 1.5, w: 1, h: 0.4,
    fontSize: 12, fontFace: "Arial", color: colors.text, bold: true,
    align: "center"
  });
  
  // 阶段名称
  overviewSlide.addText(stage.title, {
    x: xPos - 0.5, y: 2.9, w: 1.4, h: 0.5,
    fontSize: 11, fontFace: "Arial", color: colors.text,
    align: "center"
  });
  
  xPos += 2.1;
});

// 关键特征说明
overviewSlide.addText("核心演进逻辑", {
  x: 0.8, y: 3.8, w: 8.4, h: 0.5,
  fontSize: 18, fontFace: "Arial", color: colors.accent, bold: true
});

overviewSlide.addText([
  { text: "• 功能扩展：", options: { bullet: true, bold: true } },
  { text: "从单一运输 → 综合物流 → 供应链整合", options: {} },
  { text: "• 技术驱动：", options: { bullet: true, bold: true, breakLine: true } },
  { text: "机械化 → 信息化 → 智能化", options: {} },
  { text: "• 价值提升：", options: { bullet: true, bold: true, breakLine: true } },
  { text: "物流节点 → 物流中心 → 供应链枢纽", options: {} }
], {
  x: 0.8, y: 4.3, w: 8.4, h: 1.8,
  fontSize: 14, fontFace: "Arial", color: colors.text,
  lineSpacing: 28
});

// ========== 阶段1：传统物流 ==========
let stage1Slide = pres.addSlide();
stage1Slide.background = { color: colors.light };

// 标题区域
stage1Slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 1.2,
  fill: { color: "94A3B8" }
});

stage1Slide.addText("阶段一：传统物流阶段", {
  x: 0.5, y: 0.25, w: 9, h: 0.7,
  fontSize: 28, fontFace: "Arial Black", color: colors.white
});

stage1Slide.addText("20世纪40年代以来", {
  x: 6.5, y: 0.35, w: 3, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: "E2E8F0", align: "right"
});

// 内容区
stage1Slide.addText("核心特征", {
  x: 0.5, y: 1.5, w: 4, h: 0.5,
  fontSize: 20, fontFace: "Arial", color: colors.accent, bold: true
});

stage1Slide.addText([
  { text: "物流功能单一", options: { bullet: true, breakLine: true } },
  { text: "港口主要作为运输中转站", options: { bullet: true, breakLine: true } },
  { text: "物流活动处于初级形态", options: { bullet: true } }
], {
  x: 0.5, y: 2.1, w: 4, h: 2,
  fontSize: 14, fontFace: "Arial", color: colors.text,
  lineSpacing: 32
});

stage1Slide.addText("主要功能", {
  x: 5, y: 1.5, w: 4.5, h: 0.5,
  fontSize: 20, fontFace: "Arial", color: colors.accent, bold: true
});

// 功能卡片
const funcs1 = ["运输", "转运", "储存"];
let funcY = 2.1;
funcs1.forEach((func, i) => {
  stage1Slide.addShape(pres.shapes.RECTANGLE, {
    x: 5, y: funcY, w: 2, h: 0.5,
    fill: { color: colors.white },
    line: { color: "94A3B8", width: 1 }
  });
  
  stage1Slide.addText(func, {
    x: 5, y: funcY, w: 2, h: 0.5,
    fontSize: 14, fontFace: "Arial", color: colors.text,
    align: "center", valign: "middle"
  });
  
  funcY += 0.7;
});

// ========== 阶段2：配送物流 ==========
let stage2Slide = pres.addSlide();
stage2Slide.background = { color: colors.light };

// 标题区域
stage2Slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 1.2,
  fill: { color: "60A5FA" }
});

stage2Slide.addText("阶段二：配送物流阶段", {
  x: 0.5, y: 0.25, w: 9, h: 0.7,
  fontSize: 28, fontFace: "Arial Black", color: colors.white
});

stage2Slide.addText("20世纪60-80年代", {
  x: 6.5, y: 0.35, w: 3, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: "E2E8F0", align: "right"
});

// 技术驱动
stage2Slide.addText("关键技术突破", {
  x: 0.5, y: 1.5, w: 4.5, h: 0.5,
  fontSize: 18, fontFace: "Arial", color: colors.accent, bold: true
});

stage2Slide.addText([
  { text: "EDI (电子数据交换)", options: { bullet: true, breakLine: true } },
  { text: "JIT (准时生产方式)", options: { bullet: true, breakLine: true } },
  { text: "集装箱运输技术", options: { bullet: true } }
], {
  x: 0.5, y: 2.1, w: 4.5, h: 1.8,
  fontSize: 14, fontFace: "Arial", color: colors.text,
  lineSpacing: 30
});

// 功能扩展
stage2Slide.addText("功能扩展", {
  x: 5.5, y: 1.5, w: 4, h: 0.5,
  fontSize: 18, fontFace: "Arial", color: colors.accent, bold: true
});

const funcs2 = [
  "运输", "转运", "储存",
  "拆装箱", "仓储管理", "加工"
];

let func2Y = 2.1;
funcs2.forEach((func, i) => {
  let x = i < 3 ? 5.5 : 7.5;
  let y = func2Y + (i % 3) * 0.6;
  
  stage2Slide.addShape(pres.shapes.RECTANGLE, {
    x: x, y: y, w: 1.8, h: 0.45,
    fill: { color: colors.white },
    line: { color: "60A5FA", width: 1 }
  });
  
  stage2Slide.addText(func, {
    x: x, y: y, w: 1.8, h: 0.45,
    fontSize: 12, fontFace: "Arial", color: colors.text,
    align: "center", valign: "middle"
  });
});

stage2Slide.addText("港口成为集\"运输、转运、储存、拆装箱、仓储管理、加工\"功能于一体的配送中心", {
  x: 0.5, y: 4.2, w: 9, h: 0.8,
  fontSize: 13, fontFace: "Arial", color: colors.accent, italic: true,
  align: "center"
});

// ========== 阶段3：综合物流 ==========
let stage3Slide = pres.addSlide();
stage3Slide.background = { color: colors.light };

// 标题区域
stage3Slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 1.2,
  fill: { color: "3B82F6" }
});

stage3Slide.addText("阶段三：综合物流阶段", {
  x: 0.5, y: 0.25, w: 9, h: 0.7,
  fontSize: 28, fontFace: "Arial Black", color: colors.white
});

stage3Slide.addText("20世纪80-90年代", {
  x: 6.5, y: 0.35, w: 3, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: "E2E8F0", align: "right"
});

// 核心变化
stage3Slide.addText("驱动力：电子商务发展", {
  x: 0.5, y: 1.5, w: 9, h: 0.5,
  fontSize: 18, fontFace: "Arial", color: colors.accent, bold: true
});

stage3Slide.addText("物流向信息化、智能化方向发展", {
  x: 0.5, y: 2, w: 9, h: 0.4,
  fontSize: 14, fontFace: "Arial", color: colors.text
});

// 四流合一
stage3Slide.addText("现代港口成为集\"四流\"于一体的重要物流中心", {
  x: 0.5, y: 2.8, w: 9, h: 0.5,
  fontSize: 16, fontFace: "Arial", color: colors.accent, bold: true,
  align: "center"
});

const flows = [
  { name: "商品流", color: "F59E0B" },
  { name: "信息流", color: "10B981" },
  { name: "资金流", color: "EF4444" },
  { name: "人才流", color: "8B5CF6" }
];

let flowX = 1.5;
flows.forEach((flow) => {
  stage3Slide.addShape(pres.shapes.OVAL, {
    x: flowX, y: 3.5, w: 1.2, h: 1.2,
    fill: { color: flow.color }
  });
  
  stage3Slide.addText(flow.name, {
    x: flowX, y: 3.5, w: 1.2, h: 1.2,
    fontSize: 14, fontFace: "Arial Black", color: colors.white,
    align: "center", valign: "middle"
  });
  
  flowX += 1.9;
});

// ========== 阶段4：供应链物流 ==========
let stage4Slide = pres.addSlide();
stage4Slide.background = { color: colors.light };

// 标题区域
stage4Slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 1.2,
  fill: { color: colors.primary }
});

stage4Slide.addText("阶段四：港口供应链物流阶段", {
  x: 0.5, y: 0.25, w: 9, h: 0.7,
  fontSize: 28, fontFace: "Arial Black", color: colors.white
});

stage4Slide.addText("进入21世纪以来", {
  x: 6.5, y: 0.35, w: 3, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: "E2E8F0", align: "right"
});

// 时代背景
stage4Slide.addText("时代背景", {
  x: 0.5, y: 1.5, w: 4, h: 0.5,
  fontSize: 18, fontFace: "Arial", color: colors.accent, bold: true
});

stage4Slide.addText([
  { text: "经济全球化", options: { bullet: true, breakLine: true } },
  { text: "现代信息技术发展", options: { bullet: true, breakLine: true } },
  { text: "现代物流和供应链管理快速发展", options: { bullet: true } }
], {
  x: 0.5, y: 2.1, w: 4, h: 2,
  fontSize: 14, fontFace: "Arial", color: colors.text,
  lineSpacing: 32
});

// 港口转变
stage4Slide.addText("港口的战略转变", {
  x: 5, y: 1.5, w: 4.5, h: 0.5,
  fontSize: 18, fontFace: "Arial", color: colors.accent, bold: true
});

stage4Slide.addText("从单一的货物装卸和储存场所转变为", {
  x: 5, y: 2.1, w: 4.5, h: 0.4,
  fontSize: 13, fontFace: "Arial", color: colors.text
});

stage4Slide.addShape(pres.shapes.RECTANGLE, {
  x: 5, y: 2.6, w: 4.5, h: 1,
  fill: { color: colors.white },
  line: { color: colors.primary, width: 2 }
});

stage4Slide.addText("综合运输体系以及\n整个供应链中的\n重要环节", {
  x: 5, y: 2.6, w: 4.5, h: 1,
  fontSize: 14, fontFace: "Arial Black", color: colors.primary,
  align: "center", valign: "middle"
});

stage4Slide.addText("成为物流服务中心节点", {
  x: 5, y: 3.8, w: 4.5, h: 0.4,
  fontSize: 13, fontFace: "Arial", color: colors.accent, bold: true,
  align: "center"
});

// ========== 供应链概念页 ==========
let supplyChainSlide = pres.addSlide();
supplyChainSlide.background = { color: colors.white };

supplyChainSlide.addText("港口物流服务供应链", {
  x: 0.5, y: 0.4, w: 9, h: 0.8,
  fontSize: 32, fontFace: "Arial Black", color: colors.primary
});

supplyChainSlide.addText("现代港口物流的形成本质上是港口物流服务供应链的形成", {
  x: 0.5, y: 1.2, w: 9, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: colors.text, italic: true,
  align: "center"
});

// 供应链图示
supplyChainSlide.addShape(pres.shapes.RECTANGLE, {
  x: 0.8, y: 2, w: 1.8, h: 1,
  fill: { color: "E0F2FE" },
  line: { color: colors.primary, width: 2 }
});

supplyChainSlide.addText("供应商", {
  x: 0.8, y: 2, w: 1.8, h: 1,
  fontSize: 14, fontFace: "Arial", color: colors.primary,
  align: "center", valign: "middle", bold: true
});

// 箭头
supplyChainSlide.addShape(pres.shapes.LINE, {
  x: 2.8, y: 2.5, w: 0.8, h: 0,
  line: { color: colors.secondary, width: 3 }
});

// 港口中心
supplyChainSlide.addShape(pres.shapes.RECTANGLE, {
  x: 3.8, y: 1.7, w: 2.4, h: 1.6,
  fill: { color: colors.primary }
});

supplyChainSlide.addText("港口物流中心", {
  x: 3.8, y: 2, w: 2.4, h: 0.6,
  fontSize: 16, fontFace: "Arial Black", color: colors.white,
  align: "center", valign: "middle"
});

supplyChainSlide.addText("核心枢纽", {
  x: 3.8, y: 2.6, w: 2.4, h: 0.5,
  fontSize: 12, fontFace: "Arial", color: "93C5FD",
  align: "center", valign: "middle"
});

// 箭头
supplyChainSlide.addShape(pres.shapes.LINE, {
  x: 6.4, y: 2.5, w: 0.8, h: 0,
  line: { color: colors.secondary, width: 3 }
});

supplyChainSlide.addShape(pres.shapes.RECTANGLE, {
  x: 7.4, y: 2, w: 1.8, h: 1,
  fill: { color: "E0F2FE" },
  line: { color: colors.primary, width: 2 }
});

supplyChainSlide.addText("消费者", {
  x: 7.4, y: 2, w: 1.8, h: 1,
  fontSize: 14, fontFace: "Arial", color: colors.primary,
  align: "center", valign: "middle", bold: true
});

// 特征说明
supplyChainSlide.addText("服务供应链类似于制造供应链，是一种新的企业组织形态和经营方式", {
  x: 0.5, y: 4, w: 9, h: 0.8,
  fontSize: 13, fontFace: "Arial", color: colors.accent,
  align: "center"
});

// ========== 总结页 ==========
let summarySlide = pres.addSlide();
summarySlide.background = { color: colors.primary };

summarySlide.addText("演进逻辑总结", {
  x: 0.5, y: 0.5, w: 9, h: 0.8,
  fontSize: 32, fontFace: "Arial Black", color: colors.white
});

// 三个维度
const dimensions = [
  { title: "功能维度", items: "运输 → 配送 → 综合 → 供应链整合" },
  { title: "技术维度", items: "机械化 → 信息化 → 智能化" },
  { title: "价值维度", items: "物流节点 → 物流中心 → 供应链枢纽" }
];

let dimY = 1.6;
dimensions.forEach((dim, i) => {
  // 卡片背景
  summarySlide.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: dimY, w: 8.4, h: 1.1,
    fill: { color: "FFFFFF", transparency: 15 }
  });
  
  summarySlide.addText(dim.title, {
    x: 1, y: dimY + 0.1, w: 2, h: 0.4,
    fontSize: 16, fontFace: "Arial Black", color: "93C5FD"
  });
  
  summarySlide.addText(dim.items, {
    x: 3.2, y: dimY + 0.35, w: 5.8, h: 0.5,
    fontSize: 14, fontFace: "Arial", color: colors.white
  });
  
  dimY += 1.4;
});

// 结束语
summarySlide.addText("现代港口物流是全球化与信息技术发展的必然产物", {
  x: 0.5, y: 4.5, w: 9, h: 0.5,
  fontSize: 16, fontFace: "Arial", color: "93C5FD",
  align: "center", italic: true
});

// ========== 保存 ==========
pres.writeFile({ fileName: "现代港口物流的形成.pptx" });
console.log("PPT已生成: 现代港口物流的形成.pptx");

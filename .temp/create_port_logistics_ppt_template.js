const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.author = 'Kimi Claw';
pres.title = '现代港口物流的形成';

// 模板配色 - 蓝色海洋主题 + 金色强调
const colors = {
  primary: "0A3D6C",      // 深蓝背景
  primaryLight: "1A4D7C", // 浅一点的蓝
  accent: "D4A73A",       // 金色强调
  accentLight: "E8C566",  // 浅金色
  white: "FFFFFF",
  text: "F0F4F8",
  textGray: "94A3B8"
};

// ========== 封面页 ==========
let coverSlide = pres.addSlide();
coverSlide.background = { color: colors.primary };

// 左侧大标题区域（模仿模板：左大标题+年份）
coverSlide.addText("现代港口物流", {
  x: 0.8, y: 2, w: 5, h: 1.2,
  fontSize: 48, fontFace: "Arial Black", color: colors.white,
  align: "left", valign: "middle"
});

coverSlide.addText("的形成", {
  x: 0.8, y: 3.2, w: 5, h: 0.8,
  fontSize: 48, fontFace: "Arial Black", color: colors.white,
  align: "left", valign: "middle"
});

coverSlide.addText("Formation of Modern Port Logistics", {
  x: 0.8, y: 4.2, w: 5, h: 0.4,
  fontSize: 14, fontFace: "Arial", color: colors.accent,
  align: "left", valign: "middle"
});

// 右侧年份（模仿模板2025样式）
coverSlide.addText("From 1940s", {
  x: 6.5, y: 3.5, w: 3, h: 0.8,
  fontSize: 36, fontFace: "Arial", color: colors.white,
  align: "right", valign: "middle"
});

// 装饰性金色线条
coverSlide.addShape(pres.shapes.RECTANGLE, {
  x: 0.8, y: 4.7, w: 2, h: 0.05,
  fill: { color: colors.accent }
});

// 右上角小标签
coverSlide.addText("Port Logistics Evolution", {
  x: 7, y: 0.5, w: 2.5, h: 0.4,
  fontSize: 10, fontFace: "Arial", color: colors.accent,
  align: "right"
});

// ========== 目录页（4 PARTS布局） ==========
let tocSlide = pres.addSlide();
tocSlide.background = { color: colors.primary };

tocSlide.addText("CONTENTS", {
  x: 0.5, y: 0.3, w: 2, h: 0.6,
  fontSize: 20, fontFace: "Arial", color: colors.white,
  align: "left", valign: "middle"
});

const contents = [
  { part: "01", title: "传统物流", subtitle: "Traditional Logistics" },
  { part: "02", title: "配送物流", subtitle: "Distribution Logistics" },
  { part: "03", title: "综合物流", subtitle: "Integrated Logistics" },
  { part: "04", title: "供应链物流", subtitle: "Supply Chain Logistics" }
];

let colX = 0.5;
contents.forEach((item, i) => {
  // 背景块（模仿模板的4列布局）
  tocSlide.addShape(pres.shapes.RECTANGLE, {
    x: colX, y: 1.2, w: 2.2, h: 4,
    fill: { color: i % 2 === 0 ? colors.primaryLight : "0B4D7C" }
  });
  
  // PART XX
  tocSlide.addText(`PART 0${item.part}`, {
    x: colX, y: 4.2, w: 2.2, h: 0.5,
    fontSize: 24, fontFace: "Arial Black", color: colors.accent,
    align: "center", valign: "middle"
  });
  
  // 标题
  tocSlide.addText(item.title, {
    x: colX, y: 4.7, w: 2.2, h: 0.4,
    fontSize: 16, fontFace: "Arial", color: colors.white,
    align: "center", valign: "middle"
  });
  
  // 英文副标题
  tocSlide.addText(item.subtitle, {
    x: colX, y: 5.1, w: 2.2, h: 0.3,
    fontSize: 10, fontFace: "Arial", color: colors.textGray,
    align: "center", valign: "middle"
  });
  
  colX += 2.4;
});

// ========== PART 01: 传统物流阶段 ==========
let stage1Slide = pres.addSlide();
stage1Slide.background = { color: colors.primary };

// 左侧装饰条（金色）
stage1Slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 0.15, h: 5.625,
  fill: { color: colors.accent }
});

// PART标签
stage1Slide.addText("PART 01", {
  x: 0.5, y: 0.4, w: 2, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: colors.accent,
  align: "left"
});

// 主标题
stage1Slide.addText("传统物流阶段", {
  x: 0.5, y: 1, w: 5, h: 0.8,
  fontSize: 32, fontFace: "Arial Black", color: colors.white
});

stage1Slide.addText("Traditional Logistics Phase", {
  x: 0.5, y: 1.8, w: 5, h: 0.4,
  fontSize: 12, fontFace: "Arial", color: colors.accent
});

// 时间标识
stage1Slide.addText("1940s+", {
  x: 7, y: 0.5, w: 2.5, h: 0.8,
  fontSize: 48, fontFace: "Arial", color: "1A5276",
  align: "right"
});

// 核心特征（带图标的布局）
stage1Slide.addText("核心特征", {
  x: 0.5, y: 2.5, w: 4, h: 0.4,
  fontSize: 16, fontFace: "Arial", color: colors.accent, bold: true
});

const features1 = [
  "物流功能单一，以运输为主",
  "港口作为纯粹的\"运输中心\"",
  "主要功能：运输、转运、储存"
];

let featY = 3;
features1.forEach(feat => {
  // 小圆点
  stage1Slide.addShape(pres.shapes.OVAL, {
    x: 0.5, y: featY + 0.1, w: 0.12, h: 0.12,
    fill: { color: colors.accent }
  });
  
  stage1Slide.addText(feat, {
    x: 0.8, y: featY, w: 4, h: 0.4,
    fontSize: 13, fontFace: "Arial", color: colors.text
  });
  featY += 0.5;
});

// ========== PART 02: 配送物流阶段 ==========
let stage2Slide = pres.addSlide();
stage2Slide.background = { color: colors.primary };

stage2Slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 0.15, h: 5.625,
  fill: { color: colors.accent }
});

stage2Slide.addText("PART 02", {
  x: 0.5, y: 0.4, w: 2, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: colors.accent
});

stage2Slide.addText("配送物流阶段", {
  x: 0.5, y: 1, w: 5, h: 0.8,
  fontSize: 32, fontFace: "Arial Black", color: colors.white
});

stage2Slide.addText("Distribution Logistics Phase", {
  x: 0.5, y: 1.8, w: 5, h: 0.4,
  fontSize: 12, fontFace: "Arial", color: colors.accent
});

stage2Slide.addText("1960-80s", {
  x: 6.5, y: 0.5, w: 3, h: 0.8,
  fontSize: 48, fontFace: "Arial", color: "1A5276",
  align: "right"
});

// 技术突破部分（双列布局）
stage2Slide.addText("技术突破", {
  x: 0.5, y: 2.5, w: 4, h: 0.4,
  fontSize: 16, fontFace: "Arial", color: colors.accent, bold: true
});

const techs = [
  { name: "EDI", desc: "电子数据交换" },
  { name: "JIT", desc: "准时生产方式" },
  { name: "集装箱", desc: "标准化运输" }
];

let techX = 0.5;
techs.forEach(tech => {
  // 技术名称卡片
  stage2Slide.addShape(pres.shapes.RECTANGLE, {
    x: techX, y: 3, w: 1.8, h: 0.6,
    fill: { color: colors.primaryLight },
    line: { color: colors.accent, width: 1 }
  });
  
  stage2Slide.addText(tech.name, {
    x: techX, y: 3, w: 1.8, h: 0.6,
    fontSize: 14, fontFace: "Arial Black", color: colors.accent,
    align: "center", valign: "middle"
  });
  
  stage2Slide.addText(tech.desc, {
    x: techX, y: 3.7, w: 1.8, h: 0.3,
    fontSize: 10, fontFace: "Arial", color: colors.textGray,
    align: "center"
  });
  
  techX += 2.1;
});

stage2Slide.addText("港口成为集\"运输、转运、储存、拆装箱、仓储管理、加工\"功能于一体的配送中心", {
  x: 0.5, y: 4.5, w: 9, h: 0.6,
  fontSize: 12, fontFace: "Arial", color: colors.text,
  align: "left", italic: true
});

// ========== PART 03: 综合物流阶段 ==========
let stage3Slide = pres.addSlide();
stage3Slide.background = { color: colors.primary };

stage3Slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 0.15, h: 5.625,
  fill: { color: colors.accent }
});

stage3Slide.addText("PART 03", {
  x: 0.5, y: 0.4, w: 2, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: colors.accent
});

stage3Slide.addText("综合物流阶段", {
  x: 0.5, y: 1, w: 5, h: 0.8,
  fontSize: 32, fontFace: "Arial Black", color: colors.white
});

stage3Slide.addText("Integrated Logistics Phase", {
  x: 0.5, y: 1.8, w: 5, h: 0.4,
  fontSize: 12, fontFace: "Arial", color: colors.accent
});

stage3Slide.addText("1980-90s", {
  x: 6.5, y: 0.5, w: 3, h: 0.8,
  fontSize: 48, fontFace: "Arial", color: "1A5276",
  align: "right"
});

// 驱动力
stage3Slide.addText("驱动力：电子商务发展", {
  x: 0.5, y: 2.5, w: 4.5, h: 0.4,
  fontSize: 16, fontFace: "Arial", color: colors.accent, bold: true
});

stage3Slide.addText("物流向信息化、智能化方向发展", {
  x: 0.5, y: 3, w: 4.5, h: 0.3,
  fontSize: 13, fontFace: "Arial", color: colors.text
});

// 四流合一（圆形布局）
stage3Slide.addText("现代港口成为集\"四流\"于一体的重要物流中心", {
  x: 5.5, y: 2.5, w: 4, h: 0.5,
  fontSize: 13, fontFace: "Arial", color: colors.accent,
  align: "center"
});

const flows = [
  { name: "商品流", color: "F59E0B", y: 3.2 },
  { name: "信息流", color: "10B981", y: 3.2 },
  { name: "资金流", color: "EF4444", y: 4 },
  { name: "人才流", color: "8B5CF6", y: 4 }
];

let flowX = 5.5;
flows.forEach((flow, i) => {
  let y = i < 2 ? 3.2 : 4;
  let x = i % 2 === 0 ? 5.5 : 7.2;
  
  stage3Slide.addShape(pres.shapes.OVAL, {
    x: x, y: y, w: 1.3, h: 0.6,
    fill: { color: flow.color }
  });
  
  stage3Slide.addText(flow.name, {
    x: x, y: y, w: 1.3, h: 0.6,
    fontSize: 12, fontFace: "Arial Black", color: colors.white,
    align: "center", valign: "middle"
  });
});

// ========== PART 04: 供应链物流阶段 ==========
let stage4Slide = pres.addSlide();
stage4Slide.background = { color: colors.primary };

stage4Slide.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 0.15, h: 5.625,
  fill: { color: colors.accent }
});

stage4Slide.addText("PART 04", {
  x: 0.5, y: 0.4, w: 2, h: 0.5,
  fontSize: 14, fontFace: "Arial", color: colors.accent
});

stage4Slide.addText("供应链物流阶段", {
  x: 0.5, y: 1, w: 6, h: 0.8,
  fontSize: 32, fontFace: "Arial Black", color: colors.white
});

stage4Slide.addText("Supply Chain Logistics Phase", {
  x: 0.5, y: 1.8, w: 6, h: 0.4,
  fontSize: 12, fontFace: "Arial", color: colors.accent
});

stage4Slide.addText("2000s+", {
  x: 7, y: 0.5, w: 2.5, h: 0.8,
  fontSize: 48, fontFace: "Arial", color: "1A5276",
  align: "right"
});

// 时代背景
stage4Slide.addText("时代背景", {
  x: 0.5, y: 2.5, w: 4, h: 0.4,
  fontSize: 16, fontFace: "Arial", color: colors.accent, bold: true
});

const bgItems = ["经济全球化", "现代信息技术发展", "现代物流和供应链管理快速发展"];
let bgY = 3;
bgItems.forEach(item => {
  stage4Slide.addShape(pres.shapes.OVAL, {
    x: 0.5, y: bgY + 0.1, w: 0.1, h: 0.1,
    fill: { color: colors.accent }
  });
  stage4Slide.addText(item, {
    x: 0.8, y: bgY, w: 4, h: 0.4,
    fontSize: 13, fontFace: "Arial", color: colors.text
  });
  bgY += 0.5;
});

// 战略转变
stage4Slide.addText("战略转变", {
  x: 5.5, y: 2.5, w: 4, h: 0.4,
  fontSize: 16, fontFace: "Arial", color: colors.accent, bold: true
});

stage4Slide.addShape(pres.shapes.RECTANGLE, {
  x: 5.5, y: 3, w: 4, h: 1.8,
  fill: { color: colors.primaryLight },
  line: { color: colors.accent, width: 1 }
});

stage4Slide.addText("从单一的货物装卸和储存场所", {
  x: 5.7, y: 3.2, w: 3.6, h: 0.3,
  fontSize: 11, fontFace: "Arial", color: colors.textGray
});

stage4Slide.addText("↓", {
  x: 5.5, y: 3.5, w: 4, h: 0.3,
  fontSize: 16, fontFace: "Arial", color: colors.accent,
  align: "center"
});

stage4Slide.addText("转变为综合运输体系以及\n整个供应链中的重要环节", {
  x: 5.7, y: 3.9, w: 3.6, h: 0.6,
  fontSize: 12, fontFace: "Arial Black", color: colors.white,
  align: "center"
});

// ========== 时间线演进图 ==========
let timelineSlide = pres.addSlide();
timelineSlide.background = { color: colors.primary };

timelineSlide.addText("演进历程", {
  x: 0.5, y: 0.4, w: 3, h: 0.6,
  fontSize: 28, fontFace: "Arial Black", color: colors.white
});

// 时间线主轴
timelineSlide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 3, w: 8, h: 0.05,
  fill: { color: colors.accent }
});

const timeline = [
  { period: "1940+", stage: "传统物流", color: "64748B" },
  { period: "1960-80", stage: "配送物流", color: "60A5FA" },
  { period: "1980-90", stage: "综合物流", color: "3B82F6" },
  { period: "2000+", stage: "供应链物流", color: colors.accent }
];

let timeX = 1.5;
timeline.forEach((item, i) => {
  // 节点
  timelineSlide.addShape(pres.shapes.OVAL, {
    x: timeX, y: 2.85, w: 0.3, h: 0.3,
    fill: { color: item.color }
  });
  
  // 时期
  timelineSlide.addText(item.period, {
    x: timeX - 0.3, y: 2.2, w: 0.9, h: 0.3,
    fontSize: 11, fontFace: "Arial", color: colors.white,
    align: "center", bold: true
  });
  
  // 阶段名称
  timelineSlide.addText(item.stage, {
    x: timeX - 0.5, y: 3.3, w: 1.3, h: 0.4,
    fontSize: 10, fontFace: "Arial", color: colors.text,
    align: "center"
  });
  
  timeX += 2;
});

// 三个维度总结
timelineSlide.addText("演进维度", {
  x: 0.5, y: 4, w: 9, h: 0.4,
  fontSize: 16, fontFace: "Arial", color: colors.accent, bold: true
});

const dimensions = [
  { name: "功能", evo: "运输 → 配送 → 综合 → 供应链" },
  { name: "技术", evo: "机械化 → 信息化 → 智能化" },
  { name: "价值", evo: "物流节点 → 物流中心 → 供应链枢纽" }
];

let dimX = 0.8;
dimensions.forEach(dim => {
  timelineSlide.addShape(pres.shapes.RECTANGLE, {
    x: dimX, y: 4.5, w: 2.8, h: 0.8,
    fill: { color: colors.primaryLight },
    line: { color: colors.accent, width: 0.5 }
  });
  
  timelineSlide.addText(dim.name, {
    x: dimX, y: 4.55, w: 0.8, h: 0.3,
    fontSize: 11, fontFace: "Arial Black", color: colors.accent
  });
  
  timelineSlide.addText(dim.evo, {
    x: dimX, y: 4.85, w: 2.8, h: 0.4,
    fontSize: 9, fontFace: "Arial", color: colors.text,
    align: "center", valign: "middle"
  });
  
  dimX += 3;
});

// ========== 结尾页 ==========
let endSlide = pres.addSlide();
endSlide.background = { color: colors.primary };

endSlide.addText("现代港口物流", {
  x: 1, y: 2, w: 8, h: 1,
  fontSize: 48, fontFace: "Arial Black", color: colors.white,
  align: "center", valign: "middle"
});

endSlide.addText("全球化与信息技术发展的必然产物", {
  x: 1, y: 3.2, w: 8, h: 0.6,
  fontSize: 16, fontFace: "Arial", color: colors.accent,
  align: "center", valign: "middle"
});

endSlide.addShape(pres.shapes.RECTANGLE, {
  x: 4, y: 4, w: 2, h: 0.05,
  fill: { color: colors.accent }
});

// ========== 保存 ==========
pres.writeFile({ fileName: "现代港口物流的形成-模板版.pptx" });
console.log("PPT已生成: 现代港口物流的形成-模板版.pptx");

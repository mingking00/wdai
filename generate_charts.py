#!/usr/bin/env python3
"""
生成联想采购分析报告所需图表
运行后会生成4张PNG图片
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

# 创建输出目录
import os
os.makedirs('charts', exist_ok=True)

# 图1: 采购流程图（横向流程）
fig, ax = plt.subplots(figsize=(14, 3))
ax.set_xlim(0, 10)
ax.set_ylim(0, 2)
ax.axis('off')

steps = ['需求预测', '供应商评估', '询价比价', '合同签订', '订单执行', '验收入库', '付款结算']
colors = ['#4472C4', '#4472C4', '#4472C4', '#4472C4', '#4472C4', '#4472C4', '#4472C4']

for i, (step, color) in enumerate(zip(steps, colors)):
    x = i * 1.3 + 0.5
    # 绘制方框
    rect = plt.Rectangle((x, 0.5), 1, 0.8, linewidth=2, edgecolor=color, facecolor='white')
    ax.add_patch(rect)
    # 添加文字
    ax.text(x + 0.5, 0.9, step, ha='center', va='center', fontsize=11, fontweight='bold')
    # 绘制箭头
    if i < len(steps) - 1:
        ax.annotate('', xy=(x + 1.1, 0.9), xytext=(x + 1.0, 0.9),
                   arrowprops=dict(arrowstyle='->', lw=2, color='black'))

# 添加反馈箭头（虚线）
ax.annotate('', xy=(0.5, 0.4), xytext=(9.4, 0.4),
           arrowprops=dict(arrowstyle='->', lw=1.5, color='red', linestyle='--'))
ax.text(5, 0.2, '绩效评估反馈', ha='center', va='center', fontsize=10, color='red')

ax.set_title('图1 联想集团采购流程图', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('charts/01_采购流程图.png', dpi=300, bbox_inches='tight')
print('✅ 图1 生成完成: charts/01_采购流程图.png')
plt.close()

# 图2: VMI库存改善对比
fig, ax = plt.subplots(figsize=(10, 6))
categories = ['实施VMI前', '实施VMI后']
inventory_days = [14, 5]
colors = ['#FF6B6B', '#4ECDC4']

bars = ax.bar(categories, inventory_days, color=colors, width=0.5, edgecolor='black', linewidth=1.5)

# 添加数值标签
for bar, days in zip(bars, inventory_days):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
            f'{days}天', ha='center', va='bottom', fontsize=20, fontweight='bold')

ax.set_ylabel('库存周转天数（天）', fontsize=12)
ax.set_title('图2 VMI实施前后库存周转天数对比', fontsize=14, fontweight='bold')
ax.set_ylim(0, 18)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# 添加改善箭头
ax.annotate('', xy=(1, 12), xytext=(0, 12),
           arrowprops=dict(arrowstyle='->', lw=3, color='green'))
ax.text(0.5, 13.5, '改善64%', ha='center', fontsize=14, color='green', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/02_VMI库存改善.png', dpi=300, bbox_inches='tight')
print('✅ 图2 生成完成: charts/02_VMI库存改善.png')
plt.close()

# 图3: 联想vs戴尔vs惠普对比雷达图
fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))

categories = ['数字化程度', '绿色采购', '成本控制', '库存周转', '准时交付', '供应商协同']
N = len(categories)

# 三家公司数据（满分10分）
lenovo_scores = [9, 9, 9, 8, 9.5, 9]
dell_scores = [7, 6, 7, 10, 9.8, 7]
hp_scores = [8, 7, 7, 6.5, 9.3, 8]

# 计算角度
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

lenovo_scores += lenovo_scores[:1]
dell_scores += dell_scores[:1]
hp_scores += hp_scores[:1]

# 绘制
ax.plot(angles, lenovo_scores, 'o-', linewidth=2, label='联想', color='#E74C3C')
ax.fill(angles, lenovo_scores, alpha=0.25, color='#E74C3C')

ax.plot(angles, dell_scores, 'o-', linewidth=2, label='戴尔', color='#3498DB')
ax.fill(angles, dell_scores, alpha=0.25, color='#3498DB')

ax.plot(angles, hp_scores, 'o-', linewidth=2, label='惠普', color='#2ECC71')
ax.fill(angles, hp_scores, alpha=0.25, color='#2ECC71')

# 设置标签
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=11)
ax.set_ylim(0, 10)
ax.set_title('图3 联想、戴尔、惠普采购管理对比', fontsize=14, fontweight='bold', pad=30)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
ax.grid(True)

plt.tight_layout()
plt.savefig('charts/03_三家企业对比雷达图.png', dpi=300, bbox_inches='tight')
print('✅ 图3 生成完成: charts/03_三家企业对比雷达图.png')
plt.close()

# 图4: 采购成本节约与效率提升柱状图
fig, ax = plt.subplots(figsize=(12, 6))

metrics = ['采购成本\n节约率', '库存周转率\n提升', '准时交付率', '决策时间\n缩短', '物流成本\n降低']
lenovo_values = [8.5, 12, 95, 55, 20]
industry_avg = [5, 8, 90, 20, 10]

x = np.arange(len(metrics))
width = 0.35

bars1 = ax.bar(x - width/2, lenovo_values, width, label='联想', color='#E74C3C', edgecolor='black')
bars2 = ax.bar(x + width/2, industry_avg, width, label='行业平均', color='#95A5A6', edgecolor='black')

# 添加数值标签
def add_labels(bars):
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

add_labels(bars1)
add_labels(bars2)

ax.set_ylabel('百分比（%）', fontsize=12)
ax.set_title('图4 联想采购管理关键指标对比', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=10)
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_ylim(0, 110)

plt.tight_layout()
plt.savefig('charts/04_关键指标对比.png', dpi=300, bbox_inches='tight')
print('✅ 图4 生成完成: charts/04_关键指标对比.png')
plt.close()

print('\n' + '='*50)
print('🎉 所有图表生成完成！')
print('='*50)
print('\n生成的文件：')
print('1. charts/01_采购流程图.png')
print('2. charts/02_VMI库存改善.png')
print('3. charts/03_三家企业对比雷达图.png')
print('4. charts/04_关键指标对比.png')
print('\n使用说明：')
print('- 将这4张图片插入Word报告对应位置')
print('- 在Word中调整图片大小，建议宽度15cm')
print('- 为每张图片添加图题（已在图片上方标注）')

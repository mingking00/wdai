#!/usr/bin/env python3
"""
生成联想采购分析报告所需图表（英文标签版）
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams

# 设置字体
rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.unicode_minus'] = False

import os
os.makedirs('charts', exist_ok=True)

# 图1: 采购流程图
fig, ax = plt.subplots(figsize=(14, 3))
ax.set_xlim(0, 10)
ax.set_ylim(0, 2)
ax.axis('off')

# 使用英文+数字编号，避免中文显示问题
steps = ['1.Demand\nForecast', '2.Supplier\nEval', '3.RFQ\nQuote', '4.Contract\nSign', '5.PO\nExecute', '6.Receipt\nCheck', '7.Payment\nSettle']
colors = ['#4472C4'] * 7

for i, (step, color) in enumerate(zip(steps, colors)):
    x = i * 1.3 + 0.3
    rect = plt.Rectangle((x, 0.4), 1, 0.9, edgecolor=color, facecolor='white', linewidth=2)
    ax.add_patch(rect)
    ax.text(x + 0.5, 0.85, step, ha='center', va='center', fontsize=9, fontweight='bold')
    if i < len(steps) - 1:
        ax.annotate('', xy=(x + 1.05, 0.85), xytext=(x + 1.0, 0.85),
                   arrowprops=dict(arrowstyle='->', lw=2, color='black'))

# 反馈箭头
ax.annotate('', xy=(0.3, 0.25), xytext=(9.4, 0.25),
           arrowprops=dict(arrowstyle='->', lw=1.5, color='red', linestyle='--'))
ax.text(4.8, 0.1, 'Performance Feedback', ha='center', va='center', fontsize=10, color='red')

ax.set_title('Figure 1: Lenovo Procurement Process Flow', fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('charts/fig1_process.png', dpi=300, bbox_inches='tight', facecolor='white')
print('✅ Figure 1 generated')
plt.close()

# 图2: VMI库存改善
fig, ax = plt.subplots(figsize=(10, 6))
categories = ['Before VMI', 'After VMI']
inventory_days = [14, 5]
colors = ['#FF6B6B', '#4ECDC4']

bars = ax.bar(categories, inventory_days, color=colors, width=0.5, edgecolor='black', linewidth=1.5)

for bar, days in zip(bars, inventory_days):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
            f'{days} days', ha='center', va='bottom', fontsize=18, fontweight='bold')

ax.set_ylabel('Inventory Turnover Days', fontsize=12)
ax.set_title('Figure 2: VMI Implementation - Inventory Improvement', fontsize=14, fontweight='bold')
ax.set_ylim(0, 18)
ax.grid(axis='y', alpha=0.3, linestyle='--')

ax.annotate('', xy=(1, 12), xytext=(0, 12),
           arrowprops=dict(arrowstyle='->', lw=3, color='green'))
ax.text(0.5, 13.5, '64% Improvement', ha='center', fontsize=14, color='green', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/fig2_vmi.png', dpi=300, bbox_inches='tight', facecolor='white')
print('✅ Figure 2 generated')
plt.close()

# 图3: 雷达图
fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))

categories = ['Digitalization', 'Green Proc.', 'Cost Ctrl', 'Inventory', 'Delivery', 'Supplier Collab']
N = len(categories)

lenovo_scores = [9, 9, 9, 8, 9.5, 9]
dell_scores = [7, 6, 7, 10, 9.8, 7]
hp_scores = [8, 7, 7, 6.5, 9.3, 8]

angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

lenovo_scores += lenovo_scores[:1]
dell_scores += dell_scores[:1]
hp_scores += hp_scores[:1]

ax.plot(angles, lenovo_scores, 'o-', linewidth=2, label='Lenovo', color='#E74C3C')
ax.fill(angles, lenovo_scores, alpha=0.25, color='#E74C3C')

ax.plot(angles, dell_scores, 'o-', linewidth=2, label='Dell', color='#3498DB')
ax.fill(angles, dell_scores, alpha=0.25, color='#3498DB')

ax.plot(angles, hp_scores, 'o-', linewidth=2, label='HP', color='#2ECC71')
ax.fill(angles, hp_scores, alpha=0.25, color='#2ECC71')

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylim(0, 10)
ax.set_title('Figure 3: Comparison - Lenovo vs Dell vs HP', fontsize=14, fontweight='bold', pad=30)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
ax.grid(True)

plt.tight_layout()
plt.savefig('charts/fig3_radar.png', dpi=300, bbox_inches='tight', facecolor='white')
print('✅ Figure 3 generated')
plt.close()

# 图4: 关键指标对比
fig, ax = plt.subplots(figsize=(12, 6))

metrics = ['Cost Saving', 'Inventory\nTurnover', 'On-time\nDelivery', 'Decision Time\nReduction', 'Logistics Cost\nReduction']
lenovo_values = [8.5, 12, 95, 55, 20]
industry_avg = [5, 8, 90, 20, 10]

x = np.arange(len(metrics))
width = 0.35

bars1 = ax.bar(x - width/2, lenovo_values, width, label='Lenovo', color='#E74C3C', edgecolor='black')
bars2 = ax.bar(x + width/2, industry_avg, width, label='Industry Avg', color='#95A5A6', edgecolor='black')

def add_labels(bars):
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

add_labels(bars1)
add_labels(bars2)

ax.set_ylabel('Percentage (%)', fontsize=12)
ax.set_title('Figure 4: Key Performance Indicators Comparison', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=9)
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_ylim(0, 110)

plt.tight_layout()
plt.savefig('charts/fig4_kpi.png', dpi=300, bbox_inches='tight', facecolor='white')
print('✅ Figure 4 generated')
plt.close()

print('\n' + '='*50)
print('All 4 figures generated successfully!')
print('='*50)

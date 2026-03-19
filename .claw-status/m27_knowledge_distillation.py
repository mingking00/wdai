#!/usr/bin/env python3
"""
MiniMax M2.7 知识蒸馏系统 v1.0

目标: 分析M2.7的输出模式，提炼可复用的能力，内化到Kimi+wdai系统

策略:
1. 数据收集 - 多维度采样M2.7输出
2. 模式分析 - 提取结构、风格、技巧
3. 知识蒸馏 - 转化为Prompt技巧、系统规则
4. 验证迭代 - 测试内化效果

Author: wdai
"""

import os
import json
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from minimax_integration import MiniMaxAPI


@dataclass
class DistillationSample:
    """蒸馏样本"""
    task_type: str
    prompt: str
    m27_output: str
    patterns_identified: List[str]
    transferable_skills: List[str]
    timestamp: str


class M27PatternAnalyzer:
    """M2.7输出模式分析器"""
    
    # 要分析的模式
    PATTERNS = {
        "structure": [
            "表格对比",
            "分点说明",
            "代码+解释",
            "步骤分解",
            "优缺点对比",
            "示例展示"
        ],
        "style": [
            "emoji使用",
            "加粗强调",
            "代码块",
            "引用块",
            "层级标题"
        ],
        "technique": [
            "多方案对比",
            "渐进解释",
            "错误预防",
            "最佳实践",
            "性能提示"
        ]
    }
    
    def __init__(self):
        self.samples: List[DistillationSample] = []
        self.pattern_frequency = defaultdict(int)
        self.structure_templates = []
    
    def analyze_output(self, task_type: str, prompt: str, output: str) -> DistillationSample:
        """分析单个输出"""
        patterns = []
        skills = []
        
        # 1. 结构模式识别
        if re.search(r'\|[^|]+\|[^|]+\|', output):  # 表格
            patterns.append("表格对比")
            skills.append("用Markdown表格对比多方案")
        
        if re.search(r'^\s*[-*]\s', output, re.M):  # 列表
            patterns.append("分点说明")
            skills.append("结构化列表展示要点")
        
        if re.search(r'```\w*\n', output):  # 代码块
            patterns.append("代码+解释")
            skills.append("代码块配合详细注释")
        
        # 2. 风格识别
        if '**' in output:
            patterns.append("加粗强调")
            skills.append("关键概念加粗突出")
        
        if re.search(r'[😀-🿿]', output):  # emoji
            patterns.append("emoji使用")
            skills.append("适量emoji增强可读性")
        
        # 3. 技术技巧识别
        if re.search(r'(优缺点|优势|劣势|对比)', output):
            patterns.append("优缺点对比")
            skills.append("主动分析方案优缺点")
        
        if re.search(r'(注意|警告|⚠️|❌)', output):
            patterns.append("错误预防")
            skills.append(" proactively指出常见错误")
        
        if re.search(r'(示例|example|比如)', output, re.I):
            patterns.append("示例展示")
            skills.append("提供可运行示例")
        
        sample = DistillationSample(
            task_type=task_type,
            prompt=prompt,
            m27_output=output,
            patterns_identified=patterns,
            transferable_skills=skills,
            timestamp=datetime.now().isoformat()
        )
        
        self.samples.append(sample)
        
        # 更新频率统计
        for p in patterns:
            self.pattern_frequency[p] += 1
        
        return sample
    
    def generate_distillation_report(self) -> Dict:
        """生成蒸馏报告"""
        if not self.samples:
            return {"error": "没有样本"}
        
        # 统计
        total_samples = len(self.samples)
        
        # 最常出现的模式 (Top 5)
        top_patterns = sorted(
            self.pattern_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # 可转移技能汇总
        all_skills = []
        for s in self.samples:
            all_skills.extend(s.transferable_skills)
        
        unique_skills = list(set(all_skills))
        
        # 生成Prompt模板
        prompt_template = self._generate_prompt_template(top_patterns)
        
        return {
            "total_samples": total_samples,
            "top_patterns": top_patterns,
            "transferable_skills": unique_skills,
            "prompt_template": prompt_template,
            "recommendations": self._generate_recommendations(top_patterns)
        }
    
    def _generate_prompt_template(self, top_patterns: List[Tuple[str, int]]) -> str:
        """生成Prompt模板"""
        template = """你是一个专业的编程助手，在回答时：

"""
        
        # 根据高频模式添加指导
        pattern_hints = {
            "表格对比": "- 使用Markdown表格对比不同方案的优缺点",
            "分点说明": "- 用清晰的列表分点说明关键概念",
            "代码+解释": "- 提供完整代码块，配合逐行注释",
            "加粗强调": "- 关键术语和概念使用**加粗**",
            "示例展示": "- 提供可运行的具体示例",
            "错误预防": "- 主动指出常见错误和注意事项"
        }
        
        for pattern, count in top_patterns:
            if pattern in pattern_hints:
                template += pattern_hints[pattern] + "\n"
        
        template += """
回答结构：
1. 直接回答核心问题
2. 展开详细说明（使用上述格式）
3. 提供实践示例
4. 总结关键要点
"""
        
        return template
    
    def _generate_recommendations(self, top_patterns: List[Tuple[str, int]]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        pattern_names = [p[0] for p in top_patterns]
        
        if "表格对比" in pattern_names:
            recommendations.append("在对比多个方案时，主动使用Markdown表格")
        
        if "代码+解释" in pattern_names:
            recommendations.append("代码块必须配合注释和解释，不只是给出代码")
        
        if "错误预防" in pattern_names:
            recommendations.append("在给出方案时，主动添加'⚠️ 注意事项'部分")
        
        if "示例展示" in pattern_names:
            recommendations.append("每个概念都要配一个最小可运行示例")
        
        return recommendations


class KnowledgeDistillationPipeline:
    """知识蒸馏Pipeline"""
    
    # 测试任务集
    BENCHMARK_TASKS = [
        {
            "type": "代码生成",
            "prompt": "写一个Python函数实现二分查找"
        },
        {
            "type": "概念解释",
            "prompt": "解释Python中的装饰器是什么"
        },
        {
            "type": "调试",
            "prompt": "这段代码有什么问题：for i in range(10): print(i); i += 1"
        },
        {
            "type": "算法优化",
            "prompt": "如何优化这个O(n²)的排序算法"
        },
        {
            "type": "最佳实践",
            "prompt": "Python中处理文件的最佳实践是什么"
        },
        {
            "type": "对比分析",
            "prompt": "对比Python的list和tuple的区别"
        }
    ]
    
    def __init__(self, api_key: str):
        self.m27_client = MiniMaxAPI(api_key)
        self.analyzer = M27PatternAnalyzer()
    
    def collect_samples(self, num_samples: int = 6) -> List[DistillationSample]:
        """收集样本"""
        print("📚 阶段1: 收集M2.7输出样本")
        print("="*60)
        
        samples = []
        tasks = self.BENCHMARK_TASKS[:num_samples]
        
        for i, task in enumerate(tasks, 1):
            print(f"\n[{i}/{len(tasks)}] {task['type']}")
            print(f"提示: {task['prompt'][:50]}...")
            
            result = self.m27_client.chat_completion(
                messages=[{"role": "user", "content": task["prompt"]}],
                model="MiniMax-M2.7",
                max_tokens=1500
            )
            
            if result.get("success"):
                output = result["content"]
                print(f"✅ 获取成功 ({len(output)}字符)")
                
                # 分析
                sample = self.analyzer.analyze_output(
                    task_type=task["type"],
                    prompt=task["prompt"],
                    output=output
                )
                samples.append(sample)
                
                # 显示发现
                if sample.patterns_identified:
                    print(f"发现模式: {', '.join(sample.patterns_identified)}")
            else:
                print(f"❌ 失败: {result.get('error')}")
        
        return samples
    
    def distill_knowledge(self) -> Dict:
        """蒸馏知识"""
        print("\n" + "="*60)
        print("🔬 阶段2: 知识蒸馏")
        print("="*60)
        
        report = self.analyzer.generate_distillation_report()
        
        print(f"\n分析样本数: {report['total_samples']}")
        
        print(f"\n高频模式 (Top 5):")
        for pattern, count in report['top_patterns']:
            print(f"  • {pattern}: {count}次")
        
        print(f"\n可转移技能 ({len(report['transferable_skills'])}项):")
        for skill in report['transferable_skills'][:10]:
            print(f"  • {skill}")
        
        print(f"\n改进建议:")
        for rec in report['recommendations']:
            print(f"  💡 {rec}")
        
        return report
    
    def create_system_prompt(self, report: Dict) -> str:
        """创建系统Prompt"""
        print("\n" + "="*60)
        print("📝 阶段3: 生成系统Prompt")
        print("="*60)
        
        prompt = report['prompt_template']
        
        print("\n生成的Prompt模板:")
        print("-"*60)
        print(prompt)
        print("-"*60)
        
        return prompt
    
    def run_full_pipeline(self):
        """运行完整Pipeline"""
        print("="*60)
        print("🎯 MiniMax M2.7 知识蒸馏系统")
        print("="*60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. 收集样本
        self.collect_samples()
        
        # 2. 蒸馏知识
        report = self.distill_knowledge()
        
        # 3. 生成Prompt
        system_prompt = self.create_system_prompt(report)
        
        # 4. 保存结果
        self._save_results(report, system_prompt)
        
        print("\n" + "="*60)
        print("✅ 知识蒸馏完成!")
        print("="*60)
        print(f"输出文件:")
        print(f"  • 完整报告: .claw-status/distillation_report.json")
        print(f"  • 系统Prompt: .claw-status/distilled_system_prompt.md")
        
        return report, system_prompt
    
    def _save_results(self, report: Dict, prompt: str):
        """保存结果"""
        # 保存JSON报告
        report_file = "/root/.openclaw/workspace/.claw-status/distillation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 保存Prompt
        prompt_file = "/root/.openclaw/workspace/.claw-status/distilled_system_prompt.md"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write("# 从MiniMax M2.7蒸馏的系统Prompt\n\n")
            f.write(f"> 生成时间: {datetime.now().isoformat()}\n\n")
            f.write("## 核心模式\n\n")
            for pattern, count in report['top_patterns']:
                f.write(f"- **{pattern}**: {count}次\n")
            f.write("\n## 系统Prompt\n\n```\n")
            f.write(prompt)
            f.write("\n```\n\n## 改进建议\n\n")
            for rec in report['recommendations']:
                f.write(f"- {rec}\n")


def main():
    """主函数"""
    api_key = "sk-cp-t9kT6omsb2iE7XfCz3Ro798ZE2kyB0MbSR8MPhTjV4SAfsKRUmQ1T3V6DkuytzQXeCJl2NB_L22j6Y_KB1_hp9if6bePI9pg9pYflh4rcLSInNzCDQPtkb4"
    
    pipeline = KnowledgeDistillationPipeline(api_key)
    report, prompt = pipeline.run_full_pipeline()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Daily Self-Check System - 每日自检系统
定时运行，回顾过去24小时的工作

运行方式:
1. 手动: python3 daily_self_check.py
2. 定时: cron job (每天9:00运行)
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/.tools')
from self_check_runner import SelfCheckRunner, CheckStatus

class DailySelfCheck:
    """每日自检系统"""
    
    def __init__(self):
        self.workspace = "/root/.openclaw/workspace"
        self.check_runner = SelfCheckRunner()
        self.check_date = datetime.now()
        
    async def run_daily_check(self):
        """运行每日自检"""
        print("="*70)
        print(f"📅 DAILY SELF-CHECK - {self.check_date.strftime('%Y-%m-%d')}")
        print("="*70)
        
        # 1. 检查过去24小时的MEMORY更新
        print("\n[1/4] 检查过去24小时的工作记录...")
        recent_work = self._get_recent_work()
        
        # 2. 分析每项工作的潜在问题
        print("\n[2/4] 分析工作内容的潜在问题...")
        findings = []
        for work in recent_work:
            finding = self._analyze_work(work)
            if finding:
                findings.append(finding)
        
        # 3. 运行自检工具
        print("\n[3/4] 运行自检检查...")
        check_results = await self._run_checks(recent_work)
        
        # 4. 生成报告
        print("\n[4/4] 生成自检报告...")
        report = self._generate_report(recent_work, findings, check_results)
        
        # 5. 保存报告
        self._save_report(report)
        
        # 6. 输出摘要
        self._print_summary(report)
        
        return report
    
    def _get_recent_work(self) -> List[Dict]:
        """获取过去24小时的工作记录"""
        work_items = []
        
        # 检查MEMORY.md最近的修改
        memory_path = os.path.join(self.workspace, "MEMORY.md")
        if os.path.exists(memory_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(memory_path))
            if self.check_date - mtime < timedelta(hours=24):
                work_items.append({
                    "type": "memory_update",
                    "file": "MEMORY.md",
                    "time": mtime.isoformat()
                })
        
        # 检查.learning目录的新文件
        learning_dir = os.path.join(self.workspace, ".learning")
        if os.path.exists(learning_dir):
            for root, dirs, files in os.walk(learning_dir):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if self.check_date - mtime < timedelta(hours=24):
                            work_items.append({
                                "type": "learning_record",
                                "file": file,
                                "time": mtime.isoformat()
                            })
        
        return work_items
    
    def _analyze_work(self, work: Dict) -> Dict:
        """分析单项工作的潜在问题"""
        # 这里可以添加更复杂的分析逻辑
        return None
    
    async def _run_checks(self, work_items: List[Dict]) -> List[Dict]:
        """运行自检检查"""
        results = []
        
        # 对每个工作项运行检查
        for work in work_items:
            context = {
                "task_description": work.get("file", "unknown"),
                "is_new_design": "design" in work.get("file", "").lower(),
                "reasoning": "daily_review"
            }
            
            check_results = self.check_runner.run_all_checks(context)
            results.append({
                "work": work,
                "checks": check_results
            })
        
        return results
    
    def _generate_report(
        self, 
        work_items: List[Dict], 
        findings: List[Dict], 
        check_results: List[Dict]
    ) -> Dict:
        """生成自检报告"""
        
        # 统计警告数量
        total_warnings = 0
        for result in check_results:
            for check in result["checks"]:
                if check.status == CheckStatus.WARNING:
                    total_warnings += 1
        
        report = {
            "date": self.check_date.isoformat(),
            "summary": {
                "work_items_reviewed": len(work_items),
                "findings": len(findings),
                "warnings": total_warnings,
                "status": "needs_attention" if total_warnings > 0 else "ok"
            },
            "work_items": work_items,
            "findings": findings,
            "check_results": [
                {
                    "work": r["work"],
                    "checks": [
                        {
                            "name": c.check_name,
                            "status": c.status.value,
                            "message": c.message,
                            "action": c.action_required
                        }
                        for c in r["checks"]
                    ]
                }
                for r in check_results
            ],
            "recommendations": self._generate_recommendations(check_results)
        }
        
        return report
    
    def _generate_recommendations(self, check_results: List[Dict]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        for result in check_results:
            for check in result["checks"]:
                if check.status == CheckStatus.WARNING:
                    if "物理约束" in check.message:
                        recommendations.append("回顾物理现实原则，查阅相关文献")
                    elif "验证" in check.message:
                        recommendations.append("为新设计创建验证实验")
                    elif "推断" in check.message:
                        recommendations.append("寻找更多案例支持当前假设")
        
        return recommendations
    
    def _save_report(self, report: Dict):
        """保存报告"""
        report_dir = os.path.join(self.workspace, ".learning", "daily-checks")
        os.makedirs(report_dir, exist_ok=True)
        
        filename = f"daily-check-{self.check_date.strftime('%Y%m%d')}.json"
        filepath = os.path.join(report_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"   报告已保存: {filepath}")
    
    def _print_summary(self, report: Dict):
        """输出摘要"""
        print("\n" + "="*70)
        print("📊 每日自检摘要")
        print("="*70)
        
        summary = report["summary"]
        print(f"\n检查项目: {summary['work_items_reviewed']}")
        print(f"发现问题: {summary['findings']}")
        print(f"警告数量: {summary['warnings']}")
        
        if summary['status'] == 'ok':
            print("\n✅ 今日工作无异常")
        else:
            print("\n⚠️  发现潜在问题，请查看详细报告")
        
        if report["recommendations"]:
            print("\n💡 改进建议:")
            for rec in report["recommendations"]:
                print(f"   • {rec}")
        
        print("="*70)


async def main():
    """主函数"""
    checker = DailySelfCheck()
    report = await checker.run_daily_check()
    return report


if __name__ == "__main__":
    report = asyncio.run(main())

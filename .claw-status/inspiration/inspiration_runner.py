#!/usr/bin/env python3
"""
灵感摄取系统 - 统一运行入口 (Unified Runner)
整合: 调度器 + 抓取器 + 整合器 + 源管理器

使用方式:
  python3 inspiration_runner.py --mode=auto    # 自动模式（推荐）
  python3 inspiration_runner.py --mode=once    # 单次运行
  python3 inspiration_runner.py --mode=dry-run # 测试模式

Author: wdai
Version: 1.0
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))

from scheduler import get_scheduler
from source_manager import SourceManager
from empty_run_solver import EmptyRunSolver
from self_healing import SelfHealingSystem, with_healing

# 导入进化引擎
try:
    from evolution_engine import InspirationEvolutionEngine
    from risk_assessment import RiskAssessmentFramework, RiskLevel
    EVOLUTION_AVAILABLE = True
except ImportError:
    EVOLUTION_AVAILABLE = False

# 导入抓取器
try:
    from crawler_arxiv import ArxivCrawler
    from crawler_github import GitHubCrawler
    from integrator import KnowledgeIntegrator
    CRAWLERS_AVAILABLE = True
except ImportError:
    CRAWLERS_AVAILABLE = False
    print("⚠️ 抓取器模块未完全就绪，使用模拟模式")


class InspirationRunner:
    """灵感系统统一运行器"""

    def __init__(self):
        self.scheduler = get_scheduler()
        self.source_manager = SourceManager()
        self.empty_solver = EmptyRunSolver()  # 空转解决器
        self.healing = SelfHealingSystem()    # 自愈系统
        self.evolution = InspirationEvolutionEngine() if EVOLUTION_AVAILABLE else None  # 进化引擎
        self.run_dir = CLAW_STATUS / "data" / "runs"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {
            'started_at': datetime.now().isoformat(),
            'sources_processed': 0,
            'items_found': 0,
            'items_queued': 0,
            'errors': [],
            'empty_solutions_executed': 0,
            'healing_actions': 0,
            'insights_generated': 0,    # 新增：生成的洞察数
            'plans_created': 0          # 新增：创建的优化方案数
        }

    def run_auto(self, dry_run: bool = False):
        """
        自动模式 - 智能决定运行哪些源

        策略:
        1. 检查调度器，只运行到时间的源
        2. 检查过载状态，必要时跳过
        3. 逐个运行，记录结果
        4. 更新调度器状态
        """
        print("="*70)
        print(f"🤖 灵感摄取系统 - 自动模式 {'[DRY-RUN]' if dry_run else ''}")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        # 检查系统健康
        healthy, reason = self.scheduler.check_system_health()
        if not healthy:
            print(f"⚠️ {reason}")
            return {'status': 'skipped', 'reason': reason}

        # 记录运行开始
        self.scheduler.record_run_start()
        # 定义要检查的源
        sources = [
            {'id': 'arxiv', 'name': 'arXiv论文', 'fetcher': self._fetch_arxiv},
            {'id': 'github', 'name': 'GitHub项目', 'fetcher': self._fetch_github},
        ]

        all_inspirations = []

        for source in sources:
            source_id = source['id']

            # 检查是否应该运行
            should_run, reason = self.scheduler.should_crawl(source_id)

            print(f"\n📡 {source['name']}:")
            print(f"   检查: {reason}")

            if not should_run:
                print(f"   ⏭️ 跳过")
                continue

            # 执行抓取
            start_time = time.time()
            try:
                if dry_run:
                    # 模拟模式
                    items = [
                        {'title': f'模拟-{source_id}-1', 'quality': 0.7},
                        {'title': f'模拟-{source_id}-2', 'quality': 0.6}
                    ]
                else:
                    items = source['fetcher']()

                crawl_time = (time.time() - start_time) * 1000

                # 记录到调度器
                quality_scores = [item.get('quality_score', 0.5) for item in items]
                self.scheduler.record_crawl(
                    source_id=source_id,
                    new_items=len(items),
                    quality_scores=quality_scores,
                    crawl_time_ms=crawl_time,
                    success=True
                )

                print(f"   ✅ 成功 | 新发现: {len(items)} | 耗时: {crawl_time:.0f}ms")
                all_inspirations.extend(items)
                self.results['sources_processed'] += 1
                self.results['items_found'] += len(items)

                # 🎯 空转解决：如果这次没有新内容，尝试其他策略
                if len(items) == 0 and not dry_run:
                    print(f"   🔍 检测到空转，启动解决策略...")
                    empty_solutions = self._solve_empty_run(source_id, source['name'])
                    if empty_solutions:
                        all_inspirations.extend(empty_solutions)
                        self.results['items_found'] += len(empty_solutions)
                        self.results['empty_solutions_executed'] += 1

            except Exception as e:
                crawl_time = (time.time() - start_time) * 1000
                self.scheduler.record_crawl(
                    source_id=source_id,
                    new_items=0,
                    quality_scores=[],
                    crawl_time_ms=crawl_time,
                    success=False
                )
                print(f"   ❌ 失败: {str(e)[:50]}")
                self.results['errors'].append({'source': source_id, 'error': str(e)})

        # 知识整合
        if all_inspirations and not dry_run:
            print(f"\n🧠 知识整合:")
            try:
                if CRAWLERS_AVAILABLE:
                    integrator = KnowledgeIntegrator()
                    queued = integrator.process_batch(all_inspirations)
                    self.results['items_queued'] = queued
                    print(f"   ✅ 已整合 {len(all_inspirations)} 条，进入审核队列: {queued}")
                else:
                    print(f"   ℹ️ 整合器未就绪，跳过")
            except Exception as e:
                print(f"   ⚠️ 整合失败: {e}")
            
            # 🧬 灵感进化 - 分析并生成优化方案
            if self.evolution and len(all_inspirations) >= 3:
                print(f"\n🧬 灵感进化分析:")
                try:
                    evolution_result = self.evolution.process_inspirations(all_inspirations)
                    self.results['insights_generated'] = evolution_result.get('insights_found', 0)
                    self.results['plans_created'] = evolution_result.get('plans_generated', 0)
                    print(f"   📊 发现 {evolution_result.get('insights_found', 0)} 个洞察")
                    print(f"   📋 生成 {evolution_result.get('plans_generated', 0)} 个优化方案")
                    print(f"   🔧 实施 {evolution_result.get('plans_implemented', 0)} 个改进")
                except Exception as e:
                    print(f"   ⚠️ 进化分析失败: {e}")

        # 源评估
        print(f"\n📊 源评估:")
        self._evaluate_sources()

        # 保存结果
        self.results['completed_at'] = datetime.now().isoformat()
        self._save_run_result()

        # 输出摘要
        print(f"\n" + "="*70)
        print(f"📋 运行摘要:")
        print(f"   处理源: {self.results['sources_processed']}")
        print(f"   发现灵感: {self.results['items_found']}")
        print(f"   进入队列: {self.results['items_queued']}")
        if self.results.get('insights_generated', 0) > 0:
            print(f"   🧬 生成洞察: {self.results['insights_generated']}")
        if self.results.get('plans_created', 0) > 0:
            print(f"   📋 优化方案: {self.results['plans_created']}")
        print(f"   错误: {len(self.results['errors'])}")
        print(f"   下次建议运行: {self._get_next_run_recommendation()}")
        print("="*70)

        return self.results

    def _fetch_arxiv(self) -> list:
        """获取arXiv论文 - 带自愈保护"""
        if not CRAWLERS_AVAILABLE:
            return []

        def _do_fetch():
            crawler = ArxivCrawler()
            result = crawler.crawl()
            return result.records if hasattr(result, 'records') else []

        def _fallback_fetch():
            # Fallback: 使用简单HTTP请求
            print("   🔄 使用fallback抓取arXiv RSS...")
            import requests
            try:
                resp = requests.get(
                    "http://export.arxiv.org/rss/cs.AI",
                    timeout=30
                )
                # 简单解析RSS
                import re
                titles = re.findall(r'<title>(.*?)</title>', resp.text)
                return [{'title': t, 'source': 'arxiv_fallback'} for t in titles[1:6]]
            except Exception as e:
                print(f"   fallback也失败: {e}")
                return []

        return self.healing.execute_with_healing(
            operation=_do_fetch,
            source="arxiv_api",
            max_retries=3,
            fallback=_fallback_fetch
        ) or []

    def _fetch_github(self) -> list:
        """获取GitHub项目 - 带自愈保护"""
        if not CRAWLERS_AVAILABLE:
            return []

        def _do_fetch():
            crawler = GitHubCrawler()
            result = crawler.crawl()
            return result.records if hasattr(result, 'records') else []

        def _fallback_fetch():
            # Fallback: 使用GitHub公开API
            print("   🔄 使用GitHub API fallback...")
            import requests
            try:
                resp = requests.get(
                    "https://api.github.com/search/repositories",
                    params={"q": "AI OR LLM OR agent", "sort": "updated", "per_page": 10},
                    timeout=30
                )
                data = resp.json()
                return [
                    {
                        'title': item['full_name'],
                        'description': item['description'],
                        'source': 'github_fallback'
                    }
                    for item in data.get('items', [])
                ]
            except Exception as e:
                print(f"   fallback也失败: {e}")
                return []

        return self.healing.execute_with_healing(
            operation=_do_fetch,
            source="github_api",
            max_retries=3,
            fallback=_fallback_fetch
        ) or []

    def _solve_empty_run(self, source_id: str, source_name: str) -> list:
        """
        解决空转问题 - 主动寻找替代内容源
        """
        solutions = []

        # 获取当前源的空转次数
        metric = self.scheduler.metrics.get(source_id)
        consecutive_empty = metric.consecutive_empty if metric else 0

        print(f"      连续空转次数: {consecutive_empty}")

        # 获取解决方案
        solution_plans = self.empty_solver.solve_empty_run(
            source_id=source_id,
            source_type='rss' if 'arxiv' in source_id else 'github',
            consecutive_empty=consecutive_empty,
            url=''
        )

        if not solution_plans:
            print(f"      ⚠️ 暂无可用解决策略")
            return []

        # 执行前2个最优策略
        for i, plan in enumerate(solution_plans[:2], 1):
            print(f"      策略{i}: [{plan['type']}] {plan['description']}")

            # 调用解决器的执行方法
            result = self.empty_solver.execute_solution(plan)

            if result.get('status') == 'success':
                items = result.get('items', [])
                solutions.extend(items)
                print(f"         ✅ 成功获取 {len(items)} 条内容")
            elif result.get('status') == 'error':
                print(f"         ❌ 失败: {result.get('error', 'unknown')}")
            else:
                print(f"         ⏳ 模拟模式: {result.get('items_found', 0)} 条")

        return solutions

    def _evaluate_sources(self):
        """评估源质量"""
        report = self.scheduler.get_source_report()

        for src in report.get('sources', [])[:3]:
            source_id = src['id']
            metrics = {
                'total_crawls': src.get('total_crawls', 0),
                'new_items_found': src.get('new_items', 0),
                'avg_quality_score': src.get('quality_score', 0),
                'current_interval_hours': src.get('current_interval_hours', 12),
                'success_rate': src.get('success_rate', 1.0)
            }

            eval_result = self.source_manager.evaluate_source(source_id, metrics)
            print(f"   {src['grade']} {source_id}: {eval_result['recommendation']}")

    def _save_run_result(self):
        """保存运行结果"""
        filename = self.run_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
        except:
            pass

    def _get_next_run_recommendation(self) -> str:
        """获取下次运行建议"""
        schedule = self.scheduler.get_next_crawl_schedule()
        if schedule:
            next_item = schedule[0]
            return f"{next_item['wait_hours']:.1f}小时后 ({next_item['source']})"
        return "视调度而定"

    def generate_system_report(self) -> str:
        """生成系统状态报告"""
        lines = []
        lines.append("# 灵感摄取系统状态报告\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        # 调度器状态
        schedule_report = self.scheduler.get_source_report()
        lines.append("## 调度器状态\n")
        daily_stats = schedule_report.get('daily_stats', {})
        lines.append(f"- 监控源数量: {schedule_report['total_sources']}")
        lines.append(f"- 今日运行: {daily_stats.get('run_count', 0)}/{daily_stats.get('max_runs', 12)}")
        lines.append(f"- 处理项目: {daily_stats.get('items_processed', 0)}")
        lines.append(f"- 执行时间: {daily_stats.get('crawl_time_seconds', 0)}s")
        overload_reason = schedule_report.get('overload_reason', '')
        overload_status = f"⚠️ {overload_reason}" if schedule_report['overload_mode'] else "✅ 正常"
        lines.append(f"- 过载模式: {overload_status}\n")

        # 用户反馈状态
        user_fb = schedule_report.get('user_feedback', {})
        lines.append("## 用户反馈\n")
        lines.append(f"- 总反馈次数: {user_fb.get('total', 0)}")
        lines.append(f"- 连续无反馈: {user_fb.get('consecutive_no_feedback', 0)}次")
        last_fb = user_fb.get('last_feedback')
        if last_fb:
            lines.append(f"- 最后反馈: {last_fb}\n")
        else:
            lines.append("- 最后反馈: 无\n")

        # 自愈系统状态 [NEW]
        healing_report = self.healing.get_health_report()
        lines.append("## 系统健康\n")
        lines.append(f"- 状态: {healing_report['status']}")
        lines.append(f"- 24小时错误: {healing_report['recent_errors_24h']}")
        lines.append(f"- 自动恢复: {healing_report['healing_stats']['auto_recovered']}")
        lines.append(f"- 熔断次数: {healing_report['healing_stats']['circuit_breaks']}")
        if healing_report['circuit_breakers']:
            lines.append("- 熔断器状态:")
            for src, cb in healing_report['circuit_breakers'].items():
                lines.append(f"  - {src}: {cb['state']} (失败{cb['failure_count']}次)")
        lines.append("")

        # 源评估
        lines.append("## 源质量评估\n")
        lines.append("| 源 | 等级 | 质量分 | 产出 | 建议 |")
        lines.append("|----|------|--------|------|------|")
        for src in schedule_report.get('sources', [])[:5]:
            lines.append(f"| {src['id']} | {src['grade']} | {src['quality_score']} | {src['new_items']} | {src['recommendation']} |")

        lines.append("\n")

        # 源管理器状态
        health = self.source_manager.get_source_health_report()
        lines.append("## 源管理\n")
        lines.append(f"- 白名单: {health['total_whitelist']}")
        lines.append(f"- 黑名单: {health['total_blacklist']}")
        lines.append(f"- 候选源: {health['pending_candidates']}\n")

        # 扩展建议
        expansion = self.source_manager.recommend_expansion(schedule_report.get('sources', []))
        if expansion.get('missing_hot_areas'):
            lines.append("## 扩展建议\n")
            lines.append(f"**缺失热门领域**: {', '.join(expansion['missing_hot_areas'][:3])}\n")
            for rec in expansion.get('recommendations', [])[:2]:
                lines.append(f"### {rec['area']}\n")
                for src in rec.get('suggested_sources', []):
                    lines.append(f"- [{src['name']}]({src['url']}) ({src['type']})")
                lines.append("")

        # 下次运行计划
        lines.append("## 下次运行计划\n")
        schedule = self.scheduler.get_next_crawl_schedule()[:5]
        for item in schedule:
            lines.append(f"- **{item['source']}**: {item['wait_hours']:.1f}h后")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='灵感摄取系统运行器')
    parser.add_argument('--mode', choices=['auto', 'once', 'dry-run', 'report'],
                       default='auto', help='运行模式')
    parser.add_argument('--reset-overload', action='store_true',
                       help='重置过载状态')
    args = parser.parse_args()

    runner = InspirationRunner()

    if args.reset_overload:
        runner.scheduler.manual_reset_overload()
        print("✅ 过载状态已重置")
        return

    if args.mode == 'report':
        report = runner.generate_system_report()
        print(report)
        # 保存报告
        report_file = CLAW_STATUS / "data" / f"system_report_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n💾 报告已保存: {report_file}")
        return

    if args.mode == 'dry-run':
        runner.run_auto(dry_run=True)
    elif args.mode in ['auto', 'once']:
        runner.run_auto(dry_run=False)


if __name__ == "__main__":
    main()

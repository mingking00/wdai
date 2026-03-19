#!/usr/bin/env python3
"""
GitHub项目深度分析器
分析发现的Agent进化相关项目
"""

import json
import requests
from pathlib import Path
from datetime import datetime

BILIBILI_DIR = Path("/root/.openclaw/workspace/.knowledge/bilibili")
SCHEDULER_DIR = Path("/root/.openclaw/workspace/.scheduler")

def analyze_project_details(repo_name: str) -> dict:
    """获取项目详细信息"""
    url = f"https://api.github.com/repos/{repo_name}"
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'wdai-analyzer'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                'stars': data.get('stargazers_count', 0),
                'forks': data.get('forks_count', 0),
                'language': data.get('language'),
                'created_at': data.get('created_at'),
                'updated_at': data.get('updated_at'),
                'topics': data.get('topics', []),
                'has_wiki': data.get('has_wiki', False),
                'has_pages': data.get('has_pages', False),
                'open_issues': data.get('open_issues_count', 0),
                'license': data.get('license', {}).get('name') if data.get('license') else None
            }
    except Exception as e:
        print(f"  获取详情失败: {e}")
    
    return {}

def get_readme_summary(repo_name: str) -> str:
    """获取README摘要"""
    url = f"https://api.github.com/repos/{repo_name}/readme"
    headers = {
        'Accept': 'application/vnd.github.v3.raw',
        'User-Agent': 'wdai-analyzer'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            content = resp.text[:2000]  # 前2000字符
            return content
    except Exception as e:
        print(f"  获取README失败: {e}")
    
    return ""

def analyze_project(project: dict) -> dict:
    """分析单个项目"""
    name = project['name']
    print(f"\n🔍 分析: {name}")
    
    # 获取详细信息
    details = analyze_project_details(name)
    readme = get_readme_summary(name)
    
    analysis = {
        'name': name,
        'description': project['description'],
        'url': project['url'],
        'discovered_at': project['discovered_at'],
        'details': details,
        'readme_preview': readme[:500] if readme else "",
        'key_insights': [],
        'applicability_to_wdai': 0.0,  # 适用性评分 0-1
        'recommendation': ''
    }
    
    # 提取关键洞察
    desc = project.get('description', '').lower()
    
    # 关键词匹配
    keywords = {
        'agent': 'Agent架构',
        'evolution': '进化系统',
        'memory': '记忆系统',
        'multi-agent': '多Agent协作',
        'autonomous': '自主性',
        'safety': '安全机制',
        'governance': '治理框架',
        'dsl': '领域特定语言',
        'prompt': 'Prompt工程',
        'workflow': '工作流',
        'coordination': '协调机制'
    }
    
    matched_keywords = []
    for kw, label in keywords.items():
        if kw in desc:
            matched_keywords.append(label)
    
    analysis['key_insights'] = matched_keywords
    
    # 适用性评分
    score = 0.0
    if 'agent' in desc or 'autonomous' in desc:
        score += 0.3
    if 'evolution' in desc or 'self-improving' in desc:
        score += 0.3
    if 'memory' in desc or 'persistent' in desc:
        score += 0.2
    if 'safety' in desc or 'human-controlled' in desc:
        score += 0.2
    
    analysis['applicability_to_wdai'] = min(score, 1.0)
    
    # 推荐级别
    if score >= 0.7:
        analysis['recommendation'] = '高度推荐 - 核心相关'
    elif score >= 0.4:
        analysis['recommendation'] = '推荐 - 值得参考'
    else:
        analysis['recommendation'] = '参考 - 低优先级'
    
    print(f"  适用性评分: {analysis['applicability_to_wdai']:.1f}")
    print(f"  关键洞察: {', '.join(matched_keywords) if matched_keywords else '无'}")
    print(f"  推荐: {analysis['recommendation']}")
    
    return analysis

def generate_analysis_report(analyses: list) -> str:
    """生成分析报告"""
    report = []
    report.append("# GitHub Agent进化项目深度分析报告")
    report.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**分析项目数**: {len(analyses)}")
    
    # 按适用性排序
    analyses_sorted = sorted(analyses, key=lambda x: x['applicability_to_wdai'], reverse=True)
    
    report.append(f"\n## 📊 项目适用性排名")
    for i, a in enumerate(analyses_sorted, 1):
        score = a['applicability_to_wdai']
        stars = "⭐" * int(score * 5)
        report.append(f"\n{i}. **{a['name']}** {stars}")
        report.append(f"   - 适用性: {score:.1f}/1.0")
        report.append(f"   - 推荐: {a['recommendation']}")
        report.append(f"   - 关键: {', '.join(a['key_insights']) if a['key_insights'] else 'N/A'}")
    
    report.append(f"\n## 🔍 详细分析")
    
    for a in analyses_sorted:
        report.append(f"\n### {a['name']}")
        report.append(f"**GitHub**: {a['url']}")
        report.append(f"**描述**: {a['description']}")
        report.append(f"**适用性评分**: {a['applicability_to_wdai']:.2f}")
        report.append(f"**推荐级别**: {a['recommendation']}")
        
        if a['details']:
            d = a['details']
            report.append(f"\n**项目统计**:")
            report.append(f"- ⭐ Stars: {d.get('stars', 0)}")
            report.append(f"- 🍴 Forks: {d.get('forks', 0)}")
            report.append(f"- 🐛 Open Issues: {d.get('open_issues', 0)}")
            report.append(f"- 💻 主要语言: {d.get('language', 'N/A')}")
            if d.get('topics'):
                report.append(f"- 🏷️  Topics: {', '.join(d['topics'][:5])}")
        
        if a['key_insights']:
            report.append(f"\n**关键洞察**:")
            for insight in a['key_insights']:
                report.append(f"- {insight}")
        
        if a['readme_preview']:
            report.append(f"\n**README预览**:")
            report.append(f"```\n{a['readme_preview'][:300]}...\n```")
    
    report.append(f"\n## 💡 对wdai的启示")
    report.append(f"\n### 架构设计")
    
    # 提取共性设计模式
    patterns = {
        '三区安全架构': '来自 agent-evolution-protocol',
        '循环进化': '来自 circe-framework',
        '符号治理': '来自 artisan-symbolic-dsl',
        'Prompt蓝图': '来自 prompting-blueprints'
    }
    
    for pattern, source in patterns.items():
        report.append(f"- **{pattern}**: {source}")
    
    report.append(f"\n### 建议采纳")
    report.append(f"\n**高优先级**:")
    report.append(f"1. 研究 agent-evolution-protocol 的三区安全架构")
    report.append(f"2. 参考 circe-framework 的多Agent协作机制")
    report.append(f"3. 学习 prompting-blueprints 的结构化Prompt方法")
    
    report.append(f"\n**中优先级**:")
    report.append(f"4. 探索 artisan-symbolic-dsl 的符号治理思想")
    
    return '\n'.join(report)

def main():
    """主函数"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     GitHub Agent进化项目深度分析                           ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # 加载发现的项目
    projects_file = SCHEDULER_DIR / "discovered_projects.json"
    
    if not projects_file.exists():
        print("❌ 未找到项目文件")
        return
    
    with open(projects_file, 'r') as f:
        projects = json.load(f)
    
    print(f"📦 发现 {len(projects)} 个项目")
    print()
    
    # 分析每个项目
    analyses = []
    for project in projects:
        analysis = analyze_project(project)
        analyses.append(analysis)
    
    # 生成报告
    print(f"\n📝 生成分析报告...")
    report = generate_analysis_report(analyses)
    
    # 保存报告
    report_file = SCHEDULER_DIR / "github_analysis_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 同时保存详细JSON
    analysis_file = SCHEDULER_DIR / "github_analysis_detailed.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analyses, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 分析完成!")
    print(f"📄 报告: {report_file}")
    print(f"📊 详情: {analysis_file}")
    
    # 显示摘要
    print(f"\n📈 适用性摘要:")
    analyses_sorted = sorted(analyses, key=lambda x: x['applicability_to_wdai'], reverse=True)
    for a in analyses_sorted:
        score = a['applicability_to_wdai']
        bar = "█" * int(score * 10)
        print(f"  {a['name'][:40]:40s} {bar} {score:.1f}")

if __name__ == '__main__':
    main()

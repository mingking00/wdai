#!/usr/bin/env python3
"""
GitHub项目自动分析器
自动发现→分析→评分→提案
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class GitHubAutoAnalyzer:
    """GitHub项目自动分析器"""
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.path.expanduser("~/.openclaw/workspace"))
        self.discovery_dir = self.workspace / ".github_discovery"
        self.analyzed_file = self.discovery_dir / "analyzed_projects.json"
        
        self.discovery_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载已分析项目
        self.analyzed = self._load_analyzed()
    
    def _load_analyzed(self) -> Dict:
        """加载已分析项目列表"""
        if self.analyzed_file.exists():
            with open(self.analyzed_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_analyzed(self):
        """保存已分析项目列表"""
        with open(self.analyzed_file, 'w') as f:
            json.dump(self.analyzed, f, indent=2)
    
    def analyze_readme(self, repo_owner: str, repo_name: str, readme_content: str) -> Dict:
        """
        分析README内容，提取关键信息
        
        Returns:
            Dict with: description, features, tech_stack, use_cases, architecture
        """
        analysis = {
            "repo": f"{repo_owner}/{repo_name}",
            "analyzed_at": datetime.now().isoformat(),
            "description": "",
            "features": [],
            "tech_stack": [],
            "use_cases": [],
            "architecture_hints": [],
            "applicability_score": 0.0,
            "suggested_improvements": []
        }
        
        # 提取描述 (第一个段落)
        paragraphs = readme_content.split('\n\n')
        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith('#') and len(p) > 20:
                analysis["description"] = p[:500]
                break
        
        # 提取特性 (列表项)
        feature_patterns = [
            r'[-*]\s+(.+?)(?=\n|$)',  # Markdown列表
            r'\d+\.\s+(.+?)(?=\n|$)',  # 数字列表
        ]
        for pattern in feature_patterns:
            matches = re.findall(pattern, readme_content)
            for m in matches[:10]:
                if len(m) > 10 and len(m) < 200:
                    analysis["features"].append(m.strip())
        
        # 提取技术栈 (常见关键词)
        tech_keywords = [
            "python", "javascript", "typescript", "rust", "go", "java",
            "react", "vue", "angular", "node.js", "django", "flask",
            "docker", "kubernetes", "aws", "gcp", "azure",
            "llm", "ai", "ml", "nlp", "embedding", "vector",
            "cli", "api", "web", "mobile", "desktop"
        ]
        content_lower = readme_content.lower()
        for tech in tech_keywords:
            if tech in content_lower:
                analysis["tech_stack"].append(tech)
        
        # 提取架构提示
        arch_patterns = [
            r"architecture[:\s]+(.+?)(?=\n|$)",
            r"design[:\s]+(.+?)(?=\n|$)",
            r"framework[:\s]+(.+?)(?=\n|$)",
            r"pattern[:\s]+(.+?)(?=\n|$)"
        ]
        for pattern in arch_patterns:
            matches = re.findall(pattern, readme_content, re.IGNORECASE)
            analysis["architecture_hints"].extend([m.strip() for m in matches[:3]])
        
        return analysis
    
    def calculate_applicability(self, analysis: Dict) -> float:
        """
        计算项目对wdai的适用性评分 (0-1)
        
        评分维度:
        - 与AI/Agent相关度
        - 与系统架构相关度
        - 可集成性
        - 创新性
        """
        score = 0.0
        content = f"{analysis.get('description', '')} {' '.join(analysis.get('features', []))}"
        content_lower = content.lower()
        
        # AI/Agent相关 (0-0.3)
        ai_keywords = ["agent", "ai", "llm", "autonomous", "evolution", "learning", "memory"]
        ai_matches = sum(1 for k in ai_keywords if k in content_lower)
        score += min(0.3, ai_matches * 0.05)
        
        # 系统架构相关 (0-0.3)
        arch_keywords = ["architecture", "framework", "system", "protocol", "safety", "security"]
        arch_matches = sum(1 for k in arch_keywords if k in content_lower)
        score += min(0.3, arch_matches * 0.05)
        
        # 可集成性 (0-0.2)
        integration_keywords = ["cli", "api", "python", "tool", "library", "sdk"]
        int_matches = sum(1 for k in integration_keywords if k in content_lower)
        score += min(0.2, int_matches * 0.04)
        
        # 创新性 (0-0.2)
        if len(analysis.get("features", [])) >= 5:
            score += 0.1
        if len(analysis.get("architecture_hints", [])) >= 2:
            score += 0.1
        
        return round(min(1.0, score), 2)
    
    def generate_improvements(self, analysis: Dict) -> List[str]:
        """基于分析生成wdai改进建议"""
        improvements = []
        content = f"{analysis.get('description', '')} {' '.join(analysis.get('features', []))}"
        content_lower = content.lower()
        
        # 安全检查相关
        if any(k in content_lower for k in ["safety", "security", "zone", "guardrail"]):
            improvements.append("借鉴安全检查机制，完善wdai三区安全架构")
        
        # 记忆系统相关
        if any(k in content_lower for k in ["memory", "remember", "recall", "semantic"]):
            improvements.append("集成语义记忆检索，提升wdai记忆系统能力")
        
        # 进化相关
        if any(k in content_lower for k in ["evolution", "improve", "adapt", "learn"]):
            improvements.append("参考进化策略，优化wdai自改进流程")
        
        # CLI/工具相关
        if any(k in content_lower for k in ["cli", "command", "tool", "interface"]):
            improvements.append("借鉴CLI设计，统一wdai工具接口")
        
        # 监控相关
        if any(k in content_lower for k in ["monitor", "dashboard", "observability"]):
            improvements.append("增强wdai监控和可观测性")
        
        # 多Agent相关
        if any(k in content_lower for k in ["multi-agent", "orchestration", "coordination"]):
            improvements.append("改进wdai多Agent协调机制")
        
        return improvements
    
    def analyze_project(self, repo_owner: str, repo_name: str, readme_content: str) -> Dict:
        """完整分析一个项目"""
        # 检查是否已分析
        repo_key = f"{repo_owner}/{repo_name}"
        if repo_key in self.analyzed:
            return self.analyzed[repo_key]
        
        # 分析README
        analysis = self.analyze_readme(repo_owner, repo_name, readme_content)
        
        # 计算适用性
        analysis["applicability_score"] = self.calculate_applicability(analysis)
        
        # 生成改进建议
        analysis["suggested_improvements"] = self.generate_improvements(analysis)
        
        # 保存
        self.analyzed[repo_key] = analysis
        self._save_analyzed()
        
        return analysis
    
    def should_create_proposal(self, analysis: Dict, threshold: float = 0.7) -> bool:
        """判断是否应该创建进化提案"""
        return analysis.get("applicability_score", 0) >= threshold
    
    def create_evolution_proposal(self, analysis: Dict) -> Optional[str]:
        """
        为高适用性项目创建进化提案
        
        Returns:
            proposal_id or None
        """
        if not self.should_create_proposal(analysis):
            return None
        
        sys.path.insert(0, str(self.workspace / '.evolution'))
        from proposal_system import ProposalSystem
        
        ps = ProposalSystem()
        
        improvements = analysis.get("suggested_improvements", [])
        if not improvements:
            return None
        
        # 创建提案
        proposal_id = ps.create_proposal(
            title=f"基于 {analysis['repo']} 的架构改进",
            problem=f"从GitHub项目 {analysis['repo']} 发现潜在改进机会",
            solution="; ".join(improvements[:3]),
            expected_effect="提升wdai系统能力，借鉴外部优秀实践",
            risk_assessment="中低风险，借鉴成熟项目的设计模式",
            implementation_steps=[
                f"研究 {analysis['repo']} 详细实现",
                "设计wdai适配方案",
                "小规模验证",
                "全面实施",
                "效果评估"
            ],
            impact="high" if analysis["applicability_score"] > 0.8 else "medium"
        )
        
        return proposal_id
    
    def get_analysis_report(self, repo_key: str = None) -> str:
        """生成分析报告"""
        if repo_key:
            if repo_key not in self.analyzed:
                return f"项目未分析: {repo_key}"
            
            a = self.analyzed[repo_key]
            report = f"""# 项目分析报告: {repo_key}

**适用性评分**: {a['applicability_score']}/1.0

## 描述
{a['description'][:300]}...

## 特性 ({len(a['features'])})
"""
            for f in a['features'][:5]:
                report += f"- {f}\n"
            
            report += f"""
## 技术栈
{', '.join(a['tech_stack'][:10])}

## 改进建议
"""
            for i in a['suggested_improvements']:
                report += f"- {i}\n"
            
            return report
        
        # 总体报告
        report = f"""# GitHub自动分析报告

**生成时间**: {datetime.now().isoformat()}
**已分析项目**: {len(self.analyzed)}

## 高适用性项目 (≥0.7)

"""
        high_applicability = [
            (k, v) for k, v in self.analyzed.items()
            if v.get("applicability_score", 0) >= 0.7
        ]
        
        if high_applicability:
            for repo, analysis in sorted(high_applicability, key=lambda x: x[1]["applicability_score"], reverse=True):
                report += f"- **{repo}**: {analysis['applicability_score']}\n"
        else:
            report += "_暂无高适用性项目_\n"
        
        return report


# ==================== CLI接口 ====================

if __name__ == "__main__":
    import sys
    
    analyzer = GitHubAutoAnalyzer()
    
    if len(sys.argv) < 2:
        print(analyzer.get_analysis_report())
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "analyze" and len(sys.argv) >= 4:
        # python auto_analyzer.py analyze owner repo < README.md
        repo_owner = sys.argv[2]
        repo_name = sys.argv[3]
        
        if sys.stdin.isatty():
            print("请通过stdin提供README内容")
            sys.exit(1)
        
        readme = sys.stdin.read()
        analysis = analyzer.analyze_project(repo_owner, repo_name, readme)
        
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        
        # 高适用性则创建提案
        if analyzer.should_create_proposal(analysis):
            proposal_id = analyzer.create_evolution_proposal(analysis)
            if proposal_id:
                print(f"\n✅ 已自动生成进化提案: {proposal_id}")
    
    elif command == "report":
        repo = sys.argv[2] if len(sys.argv) > 2 else None
        print(analyzer.get_analysis_report(repo))
    
    elif command == "list":
        for repo, analysis in analyzer.analyzed.items():
            score = analysis.get("applicability_score", 0)
            emoji = "🔴" if score >= 0.8 else "🟡" if score >= 0.6 else "🟢"
            print(f"{emoji} {repo}: {score}")
    
    else:
        print(f"Unknown command: {command}")

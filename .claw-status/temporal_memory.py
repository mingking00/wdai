"""
时态记忆管理工具

功能：
1. 检查记忆事实的有效性
2. 计算置信度衰减
3. 提醒即将过期的事实
4. 自动归档过期事实

使用方式：
    from temporal_memory import check_fact_validity, list_expiring_facts
    
    # 检查事实是否有效
    is_valid, days_left = check_fact_validity("Railway 部署正常")
    
    # 列出即将过期的事实
    expiring = list_expiring_facts(days=7)
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TemporalFact:
    """时态事实数据结构"""
    content: str
    created_date: datetime
    valid_until: Optional[datetime]
    confidence: float
    source: str
    last_checked: Optional[datetime]
    line_number: int
    
    def is_valid(self, reference_date: datetime = None) -> bool:
        """检查事实是否仍在有效期内"""
        if self.valid_until is None:
            return True
        
        ref = reference_date or datetime.now()
        return ref <= self.valid_until
    
    def days_remaining(self, reference_date: datetime = None) -> Optional[int]:
        """返回剩余有效天数"""
        if self.valid_until is None:
            return None
        
        ref = reference_date or datetime.now()
        if ref > self.valid_until:
            return -1
        
        return (self.valid_until - ref).days
    
    def current_confidence(self, reference_date: datetime = None) -> float:
        """计算当前置信度（考虑时间衰减）"""
        if self.valid_until is None:
            return self.confidence
        
        ref = reference_date or datetime.now()
        
        # 已过期
        if ref > self.valid_until:
            return 0.0
        
        # 计算衰减
        total_valid_days = (self.valid_until - self.created_date).days
        if total_valid_days <= 0:
            return self.confidence
        
        elapsed_days = (ref - self.created_date).days
        decay_periods = elapsed_days / (total_valid_days * 0.1)  # 每10%有效期衰减一次
        
        # 每过一个衰减周期，置信度乘以 0.95
        current_conf = self.confidence * (0.95 ** decay_periods)
        return max(0.0, min(1.0, current_conf))
    
    def to_markdown(self) -> str:
        """转换回 Markdown 格式"""
        date_str = self.created_date.strftime('%Y-%m-%d')
        
        parts = [f"- [{date_str}] {self.content}"]
        
        if self.valid_until:
            # 智能格式化有效期
            days = (self.valid_until - self.created_date).days
            if days >= 365:
                parts.append(f"[valid: permanent]")
            elif days >= 30:
                parts.append(f"[valid: {days // 30} months]")
            else:
                parts.append(f"[valid: {days} days]")
        
        # 置信度
        if self.confidence >= 0.9:
            conf_str = "high"
        elif self.confidence >= 0.7:
            conf_str = "medium"
        else:
            conf_str = "low"
        parts.append(f"[confidence: {conf_str}]")
        
        # 来源
        parts.append(f"[source: {self.source}]")
        
        # 最后验证日期
        if self.last_checked:
            parts.append(f"[checked: {self.last_checked.strftime('%Y-%m-%d')}]")
        
        return " ".join(parts)


class TemporalMemoryManager:
    """时态记忆管理器"""
    
    def __init__(self, memory_dir: str = None):
        if memory_dir is None:
            self.memory_file = Path.home() / '.openclaw' / 'workspace' / 'memory' / 'core' / 'temporal_facts.md'
        else:
            self.memory_file = Path(memory_dir) / 'temporal_facts.md'
        
        self.facts: List[TemporalFact] = []
        self._load_facts()
    
    def _load_facts(self):
        """从文件加载时态事实"""
        if not self.memory_file.exists():
            return
        
        with open(self.memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析事实
        self.facts = self._parse_facts(content)
    
    def _parse_facts(self, content: str) -> List[TemporalFact]:
        """解析 Markdown 内容提取时态事实"""
        facts = []
        
        # 匹配模式: - [2026-03-18] 事实内容 [valid: ...] [confidence: ...]
        pattern = r'- \[(\d{4}-\d{2}-\d{2})\] (.+?)(?=\n- \[|$)'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            line_num = content[:match.start()].count('\n') + 1
            date_str = match.group(1)
            full_content = match.group(2).strip()
            
            # 解析各个字段
            fact_content = self._extract_content(full_content)
            valid_until = self._parse_valid_date(full_content, date_str)
            confidence = self._parse_confidence(full_content)
            source = self._parse_source(full_content)
            last_checked = self._parse_checked_date(full_content)
            
            fact = TemporalFact(
                content=fact_content,
                created_date=datetime.strptime(date_str, '%Y-%m-%d'),
                valid_until=valid_until,
                confidence=confidence,
                source=source,
                last_checked=last_checked,
                line_number=line_num
            )
            
            facts.append(fact)
        
        return facts
    
    def _extract_content(self, text: str) -> str:
        """提取事实内容（去除标记）"""
        # 移除 [valid: ...] [confidence: ...] 等标记
        content = re.sub(r'\[valid:[^\]]*\]', '', text)
        content = re.sub(r'\[confidence:[^\]]*\]', '', content)
        content = re.sub(r'\[source:[^\]]*\]', '', content)
        content = re.sub(r'\[checked:[^\]]*\]', '', content)
        return content.strip()
    
    def _parse_valid_date(self, text: str, created_date_str: str) -> Optional[datetime]:
        """解析有效期"""
        valid_match = re.search(r'\[valid:\s*([^\]]+)\]', text)
        if not valid_match:
            return None
        
        valid_str = valid_match.group(1).strip().lower()
        created = datetime.strptime(created_date_str, '%Y-%m-%d')
        
        # permanent / until next update
        if 'permanent' in valid_str or 'until' in valid_str:
            return None  # 永久有效
        
        # N days
        days_match = re.search(r'(\d+)\s*day', valid_str)
        if days_match:
            return created + timedelta(days=int(days_match.group(1)))
        
        # N months
        months_match = re.search(r'(\d+)\s*month', valid_str)
        if months_match:
            return created + timedelta(days=int(months_match.group(1)) * 30)
        
        return None
    
    def _parse_confidence(self, text: str) -> float:
        """解析置信度"""
        conf_match = re.search(r'\[confidence:\s*([^\]]+)\]', text)
        if not conf_match:
            return 0.7  # 默认值
        
        conf_str = conf_match.group(1).strip().lower()
        
        # 数值
        if conf_str.replace('.', '').isdigit():
            return float(conf_str)
        
        # 等级
        if conf_str == 'high':
            return 0.9
        elif conf_str == 'medium':
            return 0.7
        elif conf_str == 'low':
            return 0.5
        
        return 0.7
    
    def _parse_source(self, text: str) -> str:
        """解析来源"""
        source_match = re.search(r'\[source:\s*([^\]]+)\]', text)
        return source_match.group(1).strip() if source_match else "unknown"
    
    def _parse_checked_date(self, text: str) -> Optional[datetime]:
        """解析最后验证日期"""
        checked_match = re.search(r'\[checked:\s*(\d{4}-\d{2}-\d{2})\]', text)
        if checked_match:
            return datetime.strptime(checked_match.group(1), '%Y-%m-%d')
        return None
    
    def check_all_facts(self) -> Tuple[List[TemporalFact], List[TemporalFact], List[TemporalFact]]:
        """
        检查所有事实，返回分类列表
        
        Returns:
            (valid_facts, expiring_soon, expired_facts)
        """
        now = datetime.now()
        
        valid = []
        expiring = []
        expired = []
        
        for fact in self.facts:
            days_left = fact.days_remaining(now)
            
            if days_left is None:
                valid.append(fact)  # 永久有效
            elif days_left < 0:
                expired.append(fact)
            elif days_left <= 7:
                expiring.append(fact)
            else:
                valid.append(fact)
        
        return valid, expiring, expired
    
    def list_expiring(self, days: int = 7) -> List[TemporalFact]:
        """列出即将过期的事实"""
        now = datetime.now()
        return [f for f in self.facts 
                if f.days_remaining(now) is not None 
                and 0 <= f.days_remaining(now) <= days]
    
    def get_fact(self, keyword: str) -> Optional[TemporalFact]:
        """根据关键词查找事实"""
        for fact in self.facts:
            if keyword.lower() in fact.content.lower():
                return fact
        return None
    
    def print_summary(self):
        """打印时态记忆摘要"""
        valid, expiring, expired = self.check_all_facts()
        
        print("="*70)
        print("🕐 时态记忆状态")
        print("="*70)
        print(f"\n总事实数: {len(self.facts)}")
        print(f"  ✅ 有效: {len(valid)}")
        print(f"  ⚠️  即将过期: {len(expiring)}")
        print(f"  ❌ 已过期: {len(expired)}")
        
        if expiring:
            print(f"\n⚠️  即将过期的事实（7天内）:")
            for fact in expiring:
                days = fact.days_remaining()
                print(f"  - {fact.content[:50]}... ({days}天)")
        
        if expired:
            print(f"\n❌ 已过期的事实:")
            for fact in expired[:5]:  # 只显示前5个
                print(f"  - {fact.content[:50]}...")
            if len(expired) > 5:
                print(f"  ... 还有 {len(expired) - 5} 个")


# ===== 快捷函数 =====

def check_fact_validity(keyword: str) -> Tuple[bool, Optional[int]]:
    """
    检查事实有效性
    
    Returns:
        (是否有效, 剩余天数)
    """
    manager = TemporalMemoryManager()
    fact = manager.get_fact(keyword)
    
    if not fact:
        return False, None
    
    return fact.is_valid(), fact.days_remaining()


def list_expiring_facts(days: int = 7) -> List[Dict]:
    """列出即将过期的事实"""
    manager = TemporalMemoryManager()
    expiring = manager.list_expiring(days)
    
    return [{
        'content': f.content,
        'days_remaining': f.days_remaining(),
        'confidence': f.current_confidence()
    } for f in expiring]


# ===== 命令行工具 =====

def main():
    """命令行入口"""
    import sys
    
    manager = TemporalMemoryManager()
    
    if len(sys.argv) < 2:
        manager.print_summary()
        return
    
    command = sys.argv[1]
    
    if command == 'check':
        # 检查特定事实
        if len(sys.argv) < 3:
            print("Usage: python temporal_memory.py check <keyword>")
            return
        
        keyword = sys.argv[2]
        is_valid, days = check_fact_validity(keyword)
        
        if days is None:
            print(f"'{keyword}': {'✅ 有效' if is_valid else '❌ 无效'} (永久有效)")
        else:
            print(f"'{keyword}': {'✅ 有效' if is_valid else '❌ 无效'} (剩余 {days} 天)")
    
    elif command == 'expiring':
        # 列出即将过期的事实
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        facts = list_expiring_facts(days)
        
        print(f"⚠️  未来 {days} 天内过期的事实:")
        for f in facts:
            print(f"  - {f['content'][:50]}... ({f['days_remaining']}天, 置信度: {f['confidence']:.2f})")
    
    else:
        manager.print_summary()


if __name__ == "__main__":
    main()

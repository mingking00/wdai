
class ZoneManager:
    """
    三区安全架构管理器
    管理wdai在不同安全区的状态转换
    """
    
    def __init__(self):
        from datetime import datetime
        self.current_zone = "human_control"  # 默认在人类控制区
        self.zone_history = []
        
    def enter_zone(self, zone_name: str, reason: str) -> bool:
        """进入指定安全区"""
        from datetime import datetime
        if self._can_transition(self.current_zone, zone_name):
            self.zone_history.append({
                "from": self.current_zone,
                "to": zone_name,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
            self.current_zone = zone_name
            print(f"[ZoneManager] 进入 {zone_name}: {reason}")
            return True
        else:
            print(f"[ZoneManager] ❌ 无法从 {self.current_zone} 切换到 {zone_name}")
            return False
    
    def _can_transition(self, from_zone: str, to_zone: str) -> bool:
        """检查状态转换是否允许"""
        allowed_transitions = {
            "human_control": ["ai_learning", "validation"],
            "ai_learning": ["validation", "human_control"],
            "validation": ["human_control", "ai_learning"]
        }
        return to_zone in allowed_transitions.get(from_zone, [])
    
    def check_permission(self, action: str) -> bool:
        """检查当前区域是否允许某操作"""
        zone_permissions = {
            "human_control": ["full_access"],
            "ai_learning": ["read_memory", "execute_code", "update_config"],
            "validation": ["read_only", "approve", "reject"]
        }
        permissions = zone_permissions.get(self.current_zone, [])
        return action in permissions or "full_access" in permissions
    
    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "current_zone": self.current_zone,
            "zone_history_count": len(self.zone_history),
            "last_transition": self.zone_history[-1] if self.zone_history else None
        }

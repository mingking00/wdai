
class MessageBus:
    """
    Agent间消息总线
    实现CIRCE风格的异步事件驱动通信
    """
    
    def __init__(self):
        self.channels = {
            "task": [],
            "status": [],
            "result": [],
            "error": [],
            "coordination": []
        }
        self.subscribers = {}
        
    def subscribe(self, channel: str, callback):
        """订阅频道"""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)
        
    def publish(self, channel: str, message: dict):
        """发布消息到频道"""
        from datetime import datetime
        if channel not in self.channels:
            return
            
        message["timestamp"] = datetime.now().isoformat()
        message["channel"] = channel
        self.channels[channel].append(message)
        
        # 通知订阅者
        if channel in self.subscribers:
            for callback in self.subscribers[channel]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"[MessageBus] 回调错误: {e}")
                    
    def get_channel_history(self, channel: str, limit: int = 10) -> list:
        """获取频道历史消息"""
        if channel not in self.channels:
            return []
        return self.channels[channel][-limit:]

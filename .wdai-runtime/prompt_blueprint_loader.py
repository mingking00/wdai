
class PromptBlueprintLoader:
    """
    Prompt蓝图加载器
    提供结构化的Prompt模板
    """
    
    def __init__(self, blueprints_path: str = None):
        import json
        from pathlib import Path
        if blueprints_path is None:
            blueprints_path = str(Path(__file__).parent / ".knowledge" / "prompt_blueprints.json")
        
        with open(blueprints_path, 'r', encoding='utf-8') as f:
            self.blueprints = json.load(f)
    
    def get_blueprint(self, name: str) -> dict:
        """获取指定蓝图"""
        return self.blueprints.get("blueprints", {}).get(name, {})
    
    def render_blueprint(self, name: str, **kwargs) -> str:
        """渲染蓝图模板"""
        blueprint = self.get_blueprint(name)
        template = blueprint.get("template", "")
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"[模板渲染错误: 缺少参数 {e}]\n{template}"
    
    def list_blueprints(self) -> list:
        """列出所有可用蓝图"""
        return list(self.blueprints.get("blueprints", {}).keys())

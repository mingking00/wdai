
@dataclass
class ResearchConfig:
    """可配置的研究参数"""
    min_sources: int = 3
    min_experiments: int = 3
    target_success_rate: float = 0.5
    max_experiment_time: int = 300  # 5分钟
    
    @classmethod
    def from_file(cls, path: Path) -> "ResearchConfig":
        if path.exists():
            data = json.loads(path.read_text())
            return cls(**data)
        return cls()

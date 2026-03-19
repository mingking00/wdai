
class RealResearcherAgent:
    """真实API版本的Researcher"""
    
    def __init__(self, search_api_key: str, llm_client):
        self.search = SearchAgentV2(api_key=search_api_key)
        self.llm = llm_client
        self.ier = IERStorage()
    
    async def gather(self, task: ResearchTask) -> Dict:
        # 真实搜索
        search_results = await self.search.search(
            query=task.topic,
            max_results=10
        )
        
        # LLM分析相关性
        relevant = await self.llm.analyze(
            f"筛选与'{task.topic}'相关的信息",
            search_results
        )
        
        task.gathered_info = relevant
        return relevant

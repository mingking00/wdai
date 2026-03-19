"""
wdai v3.0 - 真实LLM Embedding集成指南

如何将 SimpleEmbeddingModel 替换为真实的LLM Embedding API
"""

from typing import List, Optional
import asyncio


class LLMEmbeddingAdapter:
    """
    LLM Embedding API 适配器基类
    
    子类需要实现 embed() 方法
    """
    
    def __init__(self, model: str, dim: int):
        self.model = model
        self.dim = dim
    
    async def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表 (长度 = self.dim)
        """
        raise NotImplementedError("子类必须实现 embed() 方法")
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量编码 (性能优化)
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表的列表
        """
        # 默认逐个处理，子类可覆盖为批量API调用
        return [await self.embed(t) for t in texts]


class OpenAIEmbeddingAdapter(LLMEmbeddingAdapter):
    """
    OpenAI Embedding API 适配器
    
    使用模型: text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-ada-002",
        base_url: Optional[str] = None
    ):
        super().__init__(model=model, dim=1536)  # ada-002 是 1536维
        
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("请安装OpenAI SDK: pip install openai")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        self._cache = {}  # 简单缓存
    
    async def embed(self, text: str) -> List[float]:
        """使用OpenAI API编码"""
        # 检查缓存
        if text in self._cache:
            return self._cache[text]
        
        # 调用API
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        vector = response.data[0].embedding
        
        # 缓存结果
        self._cache[text] = vector
        
        return vector
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码 - OpenAI支持批量API调用"""
        # 过滤已缓存的
        to_embed = []
        indices = []
        results = [None] * len(texts)
        
        for i, text in enumerate(texts):
            if text in self._cache:
                results[i] = self._cache[text]
            else:
                to_embed.append(text)
                indices.append(i)
        
        if not to_embed:
            return results
        
        # 批量调用API
        response = await self.client.embeddings.create(
            model=self.model,
            input=to_embed
        )
        
        # 填充结果并缓存
        for idx, data in zip(indices, response.data):
            vector = data.embedding
            results[idx] = vector
            self._cache[texts[idx]] = vector
        
        return results


class CohereEmbeddingAdapter(LLMEmbeddingAdapter):
    """
    Cohere Embedding API 适配器
    
    使用模型: embed-english-v3, embed-multilingual-v3
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "embed-english-v3",
        input_type: str = "search_document"
    ):
        super().__init__(model=model, dim=1024)  # Cohere v3 是 1024维
        
        try:
            import cohere
        except ImportError:
            raise ImportError("请安装Cohere SDK: pip install cohere")
        
        self.client = cohere.AsyncClient(api_key)
        self.input_type = input_type
        self._cache = {}
    
    async def embed(self, text: str) -> List[float]:
        """使用Cohere API编码"""
        if text in self._cache:
            return self._cache[text]
        
        response = await self.client.embed(
            texts=[text],
            model=self.model,
            input_type=self.input_type
        )
        
        vector = response.embeddings[0]
        self._cache[text] = vector
        
        return vector


class LocalEmbeddingAdapter(LLMEmbeddingAdapter):
    """
    本地Embedding模型适配器
    
    使用开源模型如: sentence-transformers, BGE, GTE
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu"
    ):
        super().__init__(model=model_name, dim=384)  # MiniLM 是 384维
        
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("请安装sentence-transformers: pip install sentence-transformers")
        
        self.model = SentenceTransformer(model_name, device=device)
        self._cache = {}
    
    def embed(self, text: str) -> List[float]:
        """
        本地模型编码 (同步API)
        
        注意: 本地模型是同步的，如果需要异步请使用线程池
        """
        if text in self._cache:
            return self._cache[text]
        
        import numpy as np
        vector = self.model.encode(text).tolist()
        
        self._cache[text] = vector
        return vector
    
    async def embed(self, text: str) -> List[float]:
        """异步包装 - 在线程池中执行"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_embed, text)
    
    def _sync_embed(self, text: str) -> List[float]:
        """同步编码"""
        import numpy as np
        return self.model.encode(text).tolist()


# ============ 使用示例 ============

async def demo_openai_embedding():
    """OpenAI Embedding 使用示例"""
    
    # 1. 创建适配器
    adapter = OpenAIEmbeddingAdapter(
        api_key="your-api-key",  # 或从环境变量读取
        model="text-embedding-ada-002"
    )
    
    # 2. 编码文本
    texts = [
        "fix authentication bug",
        "resolve login error",
        "database connection pool"
    ]
    
    vectors = await adapter.embed_batch(texts)
    
    # 3. 计算相似度
    def cosine_similarity(v1, v2):
        import math
        dot = sum(a*b for a,b in zip(v1,v2))
        norm1 = math.sqrt(sum(a*a for a in v1))
        norm2 = math.sqrt(sum(b*b for b in v2))
        return dot / (norm1 * norm2)
    
    sim = cosine_similarity(vectors[0], vectors[1])
    print(f"'fix authentication bug' vs 'resolve login error': {sim:.3f}")
    # 预期: 高相似度 (~0.8+)
    
    sim2 = cosine_similarity(vectors[0], vectors[2])
    print(f"'fix authentication bug' vs 'database connection pool': {sim2:.3f}")
    # 预期: 低相似度 (~0.3)


async def demo_with_fresh_eyes():
    """在Fresh Eyes中使用真实LLM Embedding"""
    
    import sys
    sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')
    
    from core.agent_system.context_embedding import create_embedding_context_manager
    from core.agent_system.models import Task, SubTask, TodoPlan, create_task
    
    # 1. 创建真实LLM适配器
    llm_adapter = OpenAIEmbeddingAdapter(
        api_key="sk-...",  # 替换为你的API Key
        model="text-embedding-ada-002"
    )
    
    # 2. 创建Embedding版ContextManager
    context_mgr = create_embedding_context_manager(
        max_files=5,
        embedding_model=llm_adapter
    )
    
    # 3. 准备任务
    task = create_task(
        description="修复登录认证Bug",
        goal="解决用户无法登录的问题"
    )
    
    subtask = SubTask(
        parent_id=task.id,
        type="debug",
        description="investigate why users cannot login to the system"
    )
    
    plan = TodoPlan(task_id=task.id, todos=[])
    
    # 4. 可用文件
    files = [
        "src/auth/login.py",
        "src/auth/authentication_service.py",
        "src/db/user_repository.py",
        "logs/error.log",
        "tests/test_login.py"
    ]
    
    file_contents = {
        "src/auth/login.py": "def login(username, password): ...",
        "src/auth/authentication_service.py": "class AuthService: ...",
        "src/db/user_repository.py": "class UserRepo: ...",
        "logs/error.log": "ERROR: Login failed for user 'admin' - Invalid credentials",
        "tests/test_login.py": "def test_login_success(): ..."
    }
    
    # 5. 执行Fresh Eyes (使用真实LLM Embedding)
    context = await context_mgr.narrow_context(
        task=task,
        subtask=subtask,
        plan=plan,
        available_files=files,
        file_contents=file_contents
    )
    
    print(f"选中文件: {context.relevant_files}")
    print(f"\n选择解释:\n{context_mgr.explain_selection(context)}")


# ============ 批量优化 ============

class BatchedEmbeddingAdapter:
    """
    批量Embedding适配器包装器
    
    自动批量处理请求，减少API调用次数
    """
    
    def __init__(
        self,
        base_adapter: LLMEmbeddingAdapter,
        batch_size: int = 100,
        max_wait_ms: int = 50
    ):
        self.base = base_adapter
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        
        self._queue = []
        self._futures = []
        self._lock = asyncio.Lock()
        self._task = None
    
    async def embed(self, text: str) -> List[float]:
        """异步获取Embedding，自动批量处理"""
        future = asyncio.Future()
        
        async with self._lock:
            self._queue.append(text)
            self._futures.append(future)
            
            # 触发批量处理
            if len(self._queue) >= self.batch_size:
                await self._flush()
            elif self._task is None:
                self._task = asyncio.create_task(self._delayed_flush())
        
        return await future
    
    async def _delayed_flush(self):
        """延迟刷新，等待更多请求"""
        await asyncio.sleep(self.max_wait_ms / 1000)
        await self._flush()
    
    async def _flush(self):
        """执行批量请求"""
        async with self._lock:
            if not self._queue:
                return
            
            texts = self._queue[:self.batch_size]
            futures = self._futures[:self.batch_size]
            
            self._queue = self._queue[self.batch_size:]
            self._futures = self._futures[self.batch_size:]
            
            self._task = None
        
        try:
            # 批量调用
            vectors = await self.base.embed_batch(texts)
            
            # 设置结果
            for future, vector in zip(futures, vectors):
                future.set_result(vector)
        
        except Exception as e:
            # 错误传播
            for future in futures:
                future.set_exception(e)


# ============ 配置管理 ============

class EmbeddingConfig:
    """
    Embedding配置管理
    
    从配置文件或环境变量读取
    """
    
    PROVIDERS = {
        "openai": OpenAIEmbeddingAdapter,
        "cohere": CohereEmbeddingAdapter,
        "local": LocalEmbeddingAdapter,
    }
    
    @classmethod
    def from_env(cls) -> LLMEmbeddingAdapter:
        """从环境变量创建适配器"""
        import os
        
        provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        
        if provider == "openai":
            return OpenAIEmbeddingAdapter(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
            )
        
        elif provider == "cohere":
            return CohereEmbeddingAdapter(
                api_key=os.getenv("COHERE_API_KEY"),
                model=os.getenv("COHERE_MODEL", "embed-english-v3")
            )
        
        else:  # local
            return LocalEmbeddingAdapter(
                model_name=os.getenv("LOCAL_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            )
    
    @classmethod
    def create_for_fresh_eyes(cls) -> Optional[LLMEmbeddingAdapter]:
        """
        为Fresh Eyes创建适配器
        
        根据可用性自动选择:
        1. 如果配置了OpenAI API Key，使用OpenAI
        2. 如果配置了Cohere API Key，使用Cohere
        3. 否则使用本地模型
        """
        import os
        
        if os.getenv("OPENAI_API_KEY"):
            return cls.from_env() if os.getenv("EMBEDDING_PROVIDER") == "openai" else \
                   OpenAIEmbeddingAdapter(api_key=os.getenv("OPENAI_API_KEY"))
        
        if os.getenv("COHERE_API_KEY"):
            return CohereEmbeddingAdapter(api_key=os.getenv("COHERE_API_KEY"))
        
        try:
            return LocalEmbeddingAdapter()
        except ImportError:
            print("警告: 未安装sentence-transformers，使用简化版Embedding")
            return None


# ============ 快速开始 ============

if __name__ == "__main__":
    print("=" * 60)
    print("wdai v3.0 - 真实LLM Embedding集成")
    print("=" * 60)
    print()
    print("支持的提供商:")
    print("  1. OpenAI - text-embedding-ada-002 (推荐)")
    print("  2. Cohere - embed-english-v3")
    print("  3. Local - sentence-transformers (免费)")
    print()
    print("环境变量配置:")
    print("  EMBEDDING_PROVIDER=openai")
    print("  OPENAI_API_KEY=sk-...")
    print()
    print("使用示例:")
    print("  from llm_embedding_adapters import EmbeddingConfig")
    print("  adapter = EmbeddingConfig.create_for_fresh_eyes()")
    print("  context_mgr = create_embedding_context_manager(embedding_model=adapter)")
    print()

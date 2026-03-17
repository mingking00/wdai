#!/usr/bin/env python3
"""
IER-KG: Iterative Experience Refinement with Knowledge Graph Enhancement
IER知识图谱增强系统

基于RAGFlow的GraphRAG架构，为CodeDev IER系统增加知识图谱能力

四层架构:
1. 代码实体图谱 (Code Entity Graph) - AST解析提取代码结构
2. 经验关系图谱 (Experience Relation Graph) - 经验间的语义关系
3. 多跳经验检索 (Multi-hop Experience Retrieval) - 基于图的路径推理
4. 词汇图谱 (Lexical Graph) - 经验溯源机制

Author: CodeDev Agent
Date: 2026-03-15
"""

import os
import ast
import hashlib
import json
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from datetime import datetime
from pathlib import Path

# 尝试导入Neo4j，如果没有则使用内存图
NEO4J_AVAILABLE = False
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    print("[IER-KG] Neo4j not available, using in-memory graph")

# ==================== 配置 ====================

IER_KG_DIR = Path('/root/.openclaw/workspace/skills/code-dev-agent/ier_kg')
IER_KG_DIR.mkdir(exist_ok=True)

GRAPH_DATA_FILE = IER_KG_DIR / 'graph_data.json'
ENTITY_INDEX_FILE = IER_KG_DIR / 'entity_index.json'
RELATION_INDEX_FILE = IER_KG_DIR / 'relation_index.json'

# Neo4j配置 (可通过环境变量覆盖)
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

# ==================== 枚举定义 ====================

class CodeEntityType(Enum):
    """代码实体类型"""
    MODULE = "module"
    PACKAGE = "package"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    PARAMETER = "parameter"
    CONSTANT = "constant"
    IMPORT = "import"
    DECORATOR = "decorator"

class CodeRelationType(Enum):
    """代码关系类型"""
    CALLS = "calls"                    # 调用
    INHERITS = "inherits"              # 继承
    IMPLEMENTS = "implements"          # 实现
    IMPORTS = "imports"                # 导入
    CONTAINS = "contains"              # 包含
    DEPENDS_ON = "depends_on"          # 依赖
    RETURNS = "returns"                # 返回
    USES = "uses"                      # 使用
    DECORATES = "decorates"            # 装饰
    READS = "reads"                    # 读取
    WRITES = "writes"                  # 写入

class ExperienceEntityType(Enum):
    """经验图谱实体类型"""
    PATTERN = "pattern"
    ANTI_PATTERN = "anti_pattern"
    SHORTCUT = "shortcut"
    OPTIMIZATION = "optimization"
    LESSON = "lesson"
    ERROR_PATTERN = "error_pattern"
    REFACTORING = "refactoring"
    TOOL = "tool"
    BEST_PRACTICE = "best_practice"

class ExperienceRelationType(Enum):
    """经验关系类型"""
    SOLVES = "solves"                      # 解决问题
    CAUSES = "causes"                      # 导致问题
    PREVENTS = "prevents"                  # 预防问题
    REPLACES = "replaces"                  # 替代旧方案
    REQUIRES = "requires"                  # 依赖前提
    CONFLICTS_WITH = "conflicts_with"      # 冲突互斥
    COMPLEMENTS = "complements"            # 互补增强
    SIMILAR_TO = "similar_to"              # 相似经验
    EVOLVED_FROM = "evolved_from"          # 演进来源
    APPLIES_TO = "applies_to"              # 适用于代码实体
    LEARNED_FROM = "learned_from"          # 学习来源

# ==================== 数据模型 ====================

@dataclass
class CodeEntity:
    """代码实体"""
    id: str
    name: str
    entity_type: CodeEntityType
    file_path: str
    line_start: int
    line_end: int
    signature: str
    docstring: Optional[str] = None
    code_snippet: Optional[str] = None
    parent_id: Optional[str] = None  # 父实体ID（如类中的方法）
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['entity_type'] = self.entity_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CodeEntity':
        data['entity_type'] = CodeEntityType(data['entity_type'])
        return cls(**data)

@dataclass
class CodeRelation:
    """代码关系"""
    id: str
    source_id: str
    target_id: str
    relation_type: CodeRelationType
    context: str  # 关系上下文
    line_number: Optional[int] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['relation_type'] = self.relation_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CodeRelation':
        data['relation_type'] = CodeRelationType(data['relation_type'])
        return cls(**data)

@dataclass
class ExperienceNode:
    """经验图谱节点"""
    id: str
    exp_type: ExperienceEntityType
    name: str
    description: str
    context: str
    solution: str
    code_example: Optional[str] = None
    source_task: Optional[str] = None
    reliability_score: float = 0.5  # 0-1，基于使用成功率
    usage_count: int = 0
    success_count: int = 0
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['exp_type'] = self.exp_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExperienceNode':
        data['exp_type'] = ExperienceEntityType(data['exp_type'])
        return cls(**data)
    
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count

@dataclass
class ExperienceEdge:
    """经验关系边"""
    id: str
    source_id: str
    target_id: str
    relation_type: ExperienceRelationType
    strength: float = 1.0  # 关系强度 0-1
    metadata: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['relation_type'] = self.relation_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExperienceEdge':
        data['relation_type'] = ExperienceRelationType(data['relation_type'])
        return cls(**data)

@dataclass
class ProvenanceChain:
    """溯源链"""
    id: str
    experience_id: str
    task_id: str
    file_path: str
    code_entities: List[str]  # 关联的代码实体ID
    code_hash: str  # 源代码哈希
    extraction_method: str  # 提取方法
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

# ==================== 第一层: 代码实体提取器 ====================

class CodeEntityExtractor:
    """
    代码实体提取器
    基于AST解析，类似RAGFlow的DeepDoc
    """
    
    def __init__(self):
        self.entities: List[CodeEntity] = []
        self.relations: List[CodeRelation] = []
    
    def extract(self, code: str, file_path: str) -> Tuple[List[CodeEntity], List[CodeRelation]]:
        """
        从代码中提取实体和关系
        
        Args:
            code: 源代码
            file_path: 文件路径
        
        Returns:
            (实体列表, 关系列表)
        """
        self.entities = []
        self.relations = []
        
        try:
            tree = ast.parse(code)
            self._process_ast(tree, file_path, code)
        except SyntaxError as e:
            # 语法错误时回退到正则提取
            print(f"[IER-KG] AST parse error in {file_path}: {e}")
            self._extract_regex_fallback(code, file_path)
        
        return self.entities, self.relations
    
    def _process_ast(self, tree: ast.AST, file_path: str, source_code: str):
        """处理AST节点"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._extract_class(node, file_path, source_code)
            elif isinstance(node, ast.FunctionDef):
                self._extract_function(node, file_path, source_code, None)
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                self._extract_import(node, file_path)
        
        # 第二轮：提取调用关系
        self._extract_call_relations(tree, file_path)
    
    def _extract_class(self, node: ast.ClassDef, file_path: str, source_code: str):
        """提取类定义"""
        class_id = self._generate_id(file_path, node.name, "class")
        
        # 获取类代码片段
        class_code = self._get_node_source(node, source_code)
        
        entity = CodeEntity(
            id=class_id,
            name=node.name,
            entity_type=CodeEntityType.CLASS,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno,
            signature=self._extract_class_signature(node),
            docstring=ast.get_docstring(node),
            code_snippet=class_code[:1000] if class_code else None,
            metadata={
                "bases": [self._get_name(base) for base in node.bases],
                "method_count": len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
            }
        )
        self.entities.append(entity)
        
        # 提取继承关系
        for base in node.bases:
            base_name = self._get_name(base)
            if base_name:
                rel = CodeRelation(
                    id=self._generate_relation_id(class_id, base_name, "inherits"),
                    source_id=class_id,
                    target_id=self._generate_id(file_path, base_name, "class"),
                    relation_type=CodeRelationType.INHERITS,
                    context=f"{node.name} inherits {base_name}",
                    line_number=node.lineno
                )
                self.relations.append(rel)
        
        # 提取类中的方法
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self._extract_function(item, file_path, source_code, class_id)
    
    def _extract_function(self, node: ast.FunctionDef, file_path: str, 
                          source_code: str, parent_id: Optional[str]):
        """提取函数/方法定义"""
        entity_type = CodeEntityType.METHOD if parent_id else CodeEntityType.FUNCTION
        func_id = self._generate_id(file_path, node.name, 
                                     "method" if parent_id else "function")
        
        func_code = self._get_node_source(node, source_code)
        
        entity = CodeEntity(
            id=func_id,
            name=node.name,
            entity_type=entity_type,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno,
            signature=self._extract_function_signature(node),
            docstring=ast.get_docstring(node),
            code_snippet=func_code[:1000] if func_code else None,
            parent_id=parent_id,
            metadata={
                "args": [arg.arg for arg in node.args.args],
                "decorators": [self._get_name(d) for d in node.decorator_list],
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            }
        )
        self.entities.append(entity)
        
        # 提取装饰器关系
        for decorator in node.decorator_list:
            dec_name = self._get_name(decorator)
            if dec_name:
                rel = CodeRelation(
                    id=self._generate_relation_id(func_id, dec_name, "decorates"),
                    source_id=func_id,
                    target_id=self._generate_id(file_path, dec_name, "decorator"),
                    relation_type=CodeRelationType.DECORATES,
                    context=f"@{dec_name} decorates {node.name}",
                    line_number=node.lineno
                )
                self.relations.append(rel)
    
    def _extract_import(self, node: Union[ast.Import, ast.ImportFrom], file_path: str):
        """提取导入语句"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_id = self._generate_id(file_path, alias.name, "import")
                entity = CodeEntity(
                    id=import_id,
                    name=alias.name,
                    entity_type=CodeEntityType.IMPORT,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.lineno,
                    signature=f"import {alias.name}",
                    metadata={"alias": alias.asname}
                )
                self.entities.append(entity)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = f"{module}.{alias.name}" if module else alias.name
                import_id = self._generate_id(file_path, name, "import")
                entity = CodeEntity(
                    id=import_id,
                    name=name,
                    entity_type=CodeEntityType.IMPORT,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=node.lineno,
                    signature=f"from {module} import {alias.name}",
                    metadata={"module": module, "alias": alias.asname}
                )
                self.entities.append(entity)
    
    def _extract_call_relations(self, tree: ast.AST, file_path: str):
        """提取函数调用关系"""
        entity_map = {e.name: e.id for e in self.entities}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in entity_map:
                        # 找到调用者
                        caller = self._find_enclosing_function(node)
                        if caller:
                            rel = CodeRelation(
                                id=self._generate_relation_id(caller.id, entity_map[func_name], "calls"),
                                source_id=caller.id,
                                target_id=entity_map[func_name],
                                relation_type=CodeRelationType.CALLS,
                                context=f"{caller.name} calls {func_name}()",
                                line_number=node.lineno
                            )
                            self.relations.append(rel)
    
    def _extract_regex_fallback(self, code: str, file_path: str):
        """AST解析失败时的正则回退方案"""
        # 简单提取类定义
        class_pattern = r'class\s+(\w+)\s*(?:\([^)]*\))?:'
        for match in re.finditer(class_pattern, code):
            class_name = match.group(1)
            line_num = code[:match.start()].count('\n') + 1
            entity = CodeEntity(
                id=self._generate_id(file_path, class_name, "class"),
                name=class_name,
                entity_type=CodeEntityType.CLASS,
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                signature=f"class {class_name}",
            )
            self.entities.append(entity)
        
        # 简单提取函数定义
        func_pattern = r'(?:async\s+)?def\s+(\w+)\s*\('
        for match in re.finditer(func_pattern, code):
            func_name = match.group(1)
            line_num = code[:match.start()].count('\n') + 1
            entity = CodeEntity(
                id=self._generate_id(file_path, func_name, "function"),
                name=func_name,
                entity_type=CodeEntityType.FUNCTION,
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                signature=f"def {func_name}(...)",
            )
            self.entities.append(entity)
    
    def _generate_id(self, file_path: str, name: str, entity_type: str) -> str:
        """生成实体ID"""
        content = f"{file_path}:{name}:{entity_type}"
        return f"{entity_type.upper()}_{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _generate_relation_id(self, source: str, target: str, rel_type: str) -> str:
        """生成关系ID"""
        content = f"{source}:{rel_type}:{target}"
        return f"REL_{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _get_name(self, node: ast.AST) -> Optional[str]:
        """获取节点名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return None
    
    def _get_node_source(self, node: ast.AST, source: str) -> Optional[str]:
        """获取节点的源代码"""
        try:
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                lines = source.split('\n')
                return '\n'.join(lines[node.lineno - 1:node.end_lineno])
        except:
            pass
        return None
    
    def _extract_class_signature(self, node: ast.ClassDef) -> str:
        """提取类签名"""
        bases = ", ".join([self._get_name(b) for b in node.bases if self._get_name(b)])
        if bases:
            return f"class {node.name}({bases})"
        return f"class {node.name}"
    
    def _extract_function_signature(self, node: ast.FunctionDef) -> str:
        """提取函数签名"""
        args = [arg.arg for arg in node.args.args]
        args_str = ", ".join(args)
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        return f"{prefix} {node.name}({args_str})"
    
    def _find_enclosing_function(self, node: ast.AST) -> Optional[CodeEntity]:
        """查找包含节点的函数实体"""
        # 简化实现：通过节点位置匹配
        for entity in self.entities:
            if entity.entity_type in (CodeEntityType.FUNCTION, CodeEntityType.METHOD):
                if hasattr(node, 'lineno'):
                    if entity.line_start <= node.lineno <= entity.line_end:
                        return entity
        return None


# ==================== 第二层: 经验关系管理器 ====================

class ExperienceRelationManager:
    """
    经验关系管理器
    管理经验节点之间的关系网络
    """
    
    def __init__(self):
        self.experiences: Dict[str, ExperienceNode] = {}
        self.edges: Dict[str, ExperienceEdge] = {}
        self.load()
    
    def load(self):
        """加载经验图谱数据"""
        if GRAPH_DATA_FILE.exists():
            with open(GRAPH_DATA_FILE, 'r') as f:
                data = json.load(f)
                self.experiences = {
                    k: ExperienceNode.from_dict(v) 
                    for k, v in data.get('experiences', {}).items()
                }
                self.edges = {
                    k: ExperienceEdge.from_dict(v)
                    for k, v in data.get('edges', {}).items()
                }
    
    def save(self):
        """保存经验图谱数据"""
        data = {
            'experiences': {k: v.to_dict() for k, v in self.experiences.items()},
            'edges': {k: v.to_dict() for k, v in self.edges.items()},
            'updated_at': datetime.now().isoformat()
        }
        with open(GRAPH_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_experience(self, exp_type: ExperienceEntityType, name: str,
                         description: str, context: str, solution: str,
                         code_example: Optional[str] = None,
                         tags: List[str] = None) -> ExperienceNode:
        """创建经验节点"""
        exp_id = f"EXP_{hashlib.md5(name.encode()).hexdigest()[:12]}"
        
        exp = ExperienceNode(
            id=exp_id,
            exp_type=exp_type,
            name=name,
            description=description,
            context=context,
            solution=solution,
            code_example=code_example,
            tags=tags or []
        )
        
        self.experiences[exp_id] = exp
        self.save()
        return exp
    
    def add_relation(self, source_id: str, target_id: str, 
                     relation_type: ExperienceRelationType,
                     strength: float = 1.0) -> ExperienceEdge:
        """添加经验关系"""
        edge_id = f"EDGE_{hashlib.md5(f'{source_id}:{relation_type}:{target_id}'.encode()).hexdigest()[:12]}"
        
        edge = ExperienceEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength
        )
        
        self.edges[edge_id] = edge
        self.save()
        return edge
    
    def link_experience_to_code(self, exp_id: str, code_entity_id: str):
        """链接经验到代码实体"""
        return self.add_relation(exp_id, code_entity_id, ExperienceRelationType.APPLIES_TO)
    
    def find_related_experiences(self, exp_id: str, 
                                  relation_types: List[ExperienceRelationType] = None,
                                  min_strength: float = 0.5) -> List[Tuple[ExperienceNode, ExperienceEdge]]:
        """查找相关经验"""
        results = []
        
        for edge in self.edges.values():
            if edge.source_id == exp_id or edge.target_id == exp_id:
                if relation_types and edge.relation_type not in relation_types:
                    continue
                if edge.strength < min_strength:
                    continue
                
                other_id = edge.target_id if edge.source_id == exp_id else edge.source_id
                if other_id in self.experiences:
                    results.append((self.experiences[other_id], edge))
        
        return results
    
    def get_experience_chain(self, exp_id: str, relation_type: ExperienceRelationType,
                            max_depth: int = 3) -> List[List[ExperienceNode]]:
        """
        获取经验链（如：A REQUIRES B REQUIRES C）
        
        Returns:
            所有可能的路径列表
        """
        paths = []
        
        def dfs(current_id: str, current_path: List[str], depth: int):
            if depth > max_depth:
                return
            
            for edge in self.edges.values():
                if edge.source_id == current_id and edge.relation_type == relation_type:
                    if edge.target_id not in current_path:  # 避免循环
                        new_path = current_path + [edge.target_id]
                        if edge.target_id in self.experiences:
                            paths.append(new_path)
                        dfs(edge.target_id, new_path, depth + 1)
        
        dfs(exp_id, [exp_id], 0)
        
        # 转换为ExperienceNode列表
        return [[self.experiences[eid] for eid in path if eid in self.experiences] 
                for path in paths]


# ==================== 第三层: 多跳经验检索器 ====================

class MultiHopExperienceRetriever:
    """
    多跳经验检索器
    基于图谱的多跳推理检索
    """
    
    def __init__(self, exp_manager: ExperienceRelationManager):
        self.exp_manager = exp_manager
    
    def retrieve(self, query_context: str, code_entities: List[CodeEntity] = None,
                 max_hops: int = 2, top_k: int = 10) -> List[Dict]:
        """
        多跳检索
        
        Args:
            query_context: 查询上下文（任务描述）
            code_entities: 代码实体列表
            max_hops: 最大跳数
            top_k: 返回结果数量
        
        Returns:
            检索结果列表，每个结果包含经验、路径、跳数、相关度分数
        """
        results = []
        visited = set()
        
        # 第0跳：基于标签的初步匹配
        seed_experiences = self._find_by_tags(query_context)
        for exp in seed_experiences:
            results.append({
                "experience": exp,
                "path": [exp.name],
                "hop": 0,
                "relevance_score": self._calculate_relevance(query_context, exp),
                "retrieval_method": "tag_match"
            })
            visited.add(exp.id)
        
        # 第1跳：代码实体关联的经验
        if code_entities:
            for entity in code_entities:
                entity_exps = self._find_by_code_entity(entity)
                for exp in entity_exps:
                    if exp.id not in visited:
                        results.append({
                            "experience": exp,
                            "path": [f"code:{entity.name}", exp.name],
                            "hop": 1,
                            "relevance_score": self._calculate_relevance(query_context, exp) * 0.95,
                            "retrieval_method": "code_entity_link"
                        })
                        visited.add(exp.id)
        
        # 第2跳：通过经验关系扩展
        if max_hops >= 2:
            current_level = list(visited)
            for exp_id in current_level:
                related = self.exp_manager.find_related_experiences(
                    exp_id, 
                    relation_types=[
                        ExperienceRelationType.SOLVES,
                        ExperienceRelationType.COMPLEMENTS,
                        ExperienceRelationType.REQUIRES
                    ]
                )
                for rel_exp, edge in related:
                    if rel_exp.id not in visited:
                        # 关系权重调整
                        relation_weight = self._get_relation_weight(edge.relation_type)
                        hop_penalty = 0.85  # 每跳衰减
                        
                        results.append({
                            "experience": rel_exp,
                            "path": self._build_path(exp_id, rel_exp, edge),
                            "hop": 2,
                            "relevance_score": self._calculate_relevance(query_context, rel_exp) * hop_penalty * relation_weight,
                            "retrieval_method": f"relation:{edge.relation_type.value}",
                            "relation_edge": edge
                        })
                        visited.add(rel_exp.id)
        
        # 第3跳：因果关系和预防关系
        if max_hops >= 3:
            second_level = [r["experience"].id for r in results if r["hop"] == 2]
            for exp_id in second_level:
                related = self.exp_manager.find_related_experiences(
                    exp_id,
                    relation_types=[
                        ExperienceRelationType.CAUSES,
                        ExperienceRelationType.PREVENTS
                    ]
                )
                for rel_exp, edge in related:
                    if rel_exp.id not in visited:
                        results.append({
                            "experience": rel_exp,
                            "path": self._build_extended_path(results, exp_id, rel_exp, edge),
                            "hop": 3,
                            "relevance_score": self._calculate_relevance(query_context, rel_exp) * 0.72,
                            "retrieval_method": f"causal:{edge.relation_type.value}"
                        })
                        visited.add(rel_exp.id)
        
        # 排序和筛选
        results.sort(key=lambda x: (-x["relevance_score"], x["hop"]))
        return results[:top_k]
    
    def _find_by_tags(self, query: str) -> List[ExperienceNode]:
        """基于标签匹配查找经验"""
        query_words = set(query.lower().split())
        matches = []
        
        for exp in self.exp_manager.experiences.values():
            exp_tags = set(tag.lower() for tag in exp.tags)
            # 计算Jaccard相似度
            intersection = query_words & exp_tags
            union = query_words | exp_tags
            if union:
                similarity = len(intersection) / len(union)
                if similarity > 0.1:  # 阈值
                    matches.append((exp, similarity))
        
        matches.sort(key=lambda x: -x[1])
        return [m[0] for m in matches[:5]]
    
    def _find_by_code_entity(self, entity: CodeEntity) -> List[ExperienceNode]:
        """通过代码实体查找关联经验"""
        results = []
        entity_id = entity.id
        
        for edge in self.exp_manager.edges.values():
            if edge.relation_type == ExperienceRelationType.APPLIES_TO:
                if edge.target_id == entity_id and edge.source_id in self.exp_manager.experiences:
                    results.append(self.exp_manager.experiences[edge.source_id])
        
        return results
    
    def _calculate_relevance(self, query: str, exp: ExperienceNode) -> float:
        """计算查询与经验的相关度"""
        query_lower = query.lower()
        
        # 多维度评分
        scores = []
        
        # 1. 名称匹配
        if exp.name.lower() in query_lower:
            scores.append(1.0)
        elif any(word in exp.name.lower() for word in query_lower.split()):
            scores.append(0.7)
        
        # 2. 描述匹配
        if exp.description.lower() in query_lower:
            scores.append(0.9)
        elif any(word in exp.description.lower() for word in query_lower.split()):
            scores.append(0.6)
        
        # 3. 上下文匹配
        if any(word in exp.context.lower() for word in query_lower.split()):
            scores.append(0.5)
        
        # 4. 标签匹配
        exp_tags = set(tag.lower() for tag in exp.tags)
        query_words = set(query_lower.split())
        if exp_tags & query_words:
            scores.append(0.8)
        
        # 5. 可靠性加成
        reliability_bonus = exp.reliability_score * 0.1
        
        if scores:
            return max(scores) + reliability_bonus
        return 0.1 + reliability_bonus
    
    def _get_relation_weight(self, rel_type: ExperienceRelationType) -> float:
        """获取关系类型权重"""
        weights = {
            ExperienceRelationType.SOLVES: 1.0,
            ExperienceRelationType.COMPLEMENTS: 0.95,
            ExperienceRelationType.REQUIRES: 0.9,
            ExperienceRelationType.REPLACES: 0.85,
            ExperienceRelationType.SIMILAR_TO: 0.8,
            ExperienceRelationType.CAUSES: 0.7,
            ExperienceRelationType.PREVENTS: 0.75,
            ExperienceRelationType.CONFLICTS_WITH: 0.3,
        }
        return weights.get(rel_type, 0.5)
    
    def _build_path(self, source_id: str, target: ExperienceNode, 
                    edge: ExperienceEdge) -> List[str]:
        """构建路径描述"""
        source = self.exp_manager.experiences.get(source_id)
        if source:
            return [source.name, f"--{edge.relation_type.value}-->", target.name]
        return [target.name]
    
    def _build_extended_path(self, existing_results: List[Dict], 
                            source_id: str, target: ExperienceNode,
                            edge: ExperienceEdge) -> List[str]:
        """构建扩展路径"""
        # 找到source_id的完整路径
        for result in existing_results:
            if result["experience"].id == source_id:
                return result["path"] + [f"--{edge.relation_type.value}-->", target.name]
        return [target.name]


# ==================== 第四层: 溯源系统 ====================

class ExperienceProvenanceSystem:
    """
    经验溯源系统
    建立经验到源代码的精确溯源链
    """
    
    def __init__(self):
        self.chains: Dict[str, ProvenanceChain] = {}
        self.provenance_file = IER_KG_DIR / 'provenance_chains.json'
        self.load()
    
    def load(self):
        """加载溯源数据"""
        if self.provenance_file.exists():
            with open(self.provenance_file, 'r') as f:
                data = json.load(f)
                self.chains = {
                    k: ProvenanceChain(**v) for k, v in data.items()
                }
    
    def save(self):
        """保存溯源数据"""
        with open(self.provenance_file, 'w') as f:
            json.dump(
                {k: asdict(v) for k, v in self.chains.items()},
                f, indent=2, ensure_ascii=False
            )
    
    def create_provenance(self, experience_id: str, task_id: str,
                         file_path: str, code_entities: List[CodeEntity],
                         source_code: str, extraction_method: str = "llm") -> ProvenanceChain:
        """创建溯源链"""
        chain_id = f"PROV_{hashlib.md5(f'{experience_id}:{task_id}'.encode()).hexdigest()[:12]}"
        
        chain = ProvenanceChain(
            id=chain_id,
            experience_id=experience_id,
            task_id=task_id,
            file_path=file_path,
            code_entities=[e.id for e in code_entities],
            code_hash=hashlib.md5(source_code.encode()).hexdigest(),
            extraction_method=extraction_method,
            confidence=0.8 if extraction_method == "ast" else 0.6
        )
        
        self.chains[chain_id] = chain
        self.save()
        return chain
    
    def trace_experience(self, experience_id: str) -> Dict:
        """溯源经验的完整来源"""
        chains = [c for c in self.chains.values() if c.experience_id == experience_id]
        
        return {
            "experience_id": experience_id,
            "provenance_count": len(chains),
            "chains": [
                {
                    "task_id": c.task_id,
                    "file_path": c.file_path,
                    "code_entities": c.code_entities,
                    "code_hash": c.code_hash[:8],
                    "extraction_method": c.extraction_method,
                    "confidence": c.confidence,
                    "created_at": c.created_at
                }
                for c in sorted(chains, key=lambda x: x.created_at, reverse=True)
            ]
        }
    
    def find_experiences_by_code(self, file_path: str, 
                                 line_number: Optional[int] = None) -> List[str]:
        """通过代码位置查找相关经验"""
        results = []
        
        for chain in self.chains.values():
            if chain.file_path == file_path:
                if line_number is None:
                    results.append(chain.experience_id)
                else:
                    # 检查行号是否在代码实体范围内
                    # 这里简化处理，实际需要查询CodeEntity
                    results.append(chain.experience_id)
        
        return list(set(results))
    
    def visualize_provenance(self, experience_id: str) -> str:
        """生成溯源可视化文本"""
        trace = self.trace_experience(experience_id)
        
        lines = [
            f"经验溯源: {experience_id}",
            "=" * 50,
            f"总溯源链数: {trace['provenance_count']}",
            ""
        ]
        
        for i, chain in enumerate(trace['chains'], 1):
            lines.extend([
                f"溯源链 #{i}",
                f"  任务: {chain['task_id']}",
                f"  文件: {chain['file_path']}",
                f"  代码哈希: {chain['code_hash']}",
                f"  提取方法: {chain['extraction_method']}",
                f"  置信度: {chain['confidence']:.2f}",
                f"  创建时间: {chain['created_at']}",
                ""
            ])
        
        return "\n".join(lines)


# ==================== 主控制器: IER知识图谱系统 ====================

class IERKnowledgeGraphSystem:
    """
    IER知识图谱系统主控制器
    整合四层架构
    """
    
    def __init__(self, use_neo4j: bool = False):
        self.use_neo4j = use_neo4j and NEO4J_AVAILABLE
        
        # 初始化各层组件
        self.code_extractor = CodeEntityExtractor()
        self.exp_manager = ExperienceRelationManager()
        self.retriever = MultiHopExperienceRetriever(self.exp_manager)
        self.provenance = ExperienceProvenanceSystem()
        
        # Neo4j连接（如果可用）
        self.neo4j_driver = None
        if self.use_neo4j:
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
                )
                print("[IER-KG] Neo4j connected successfully")
            except Exception as e:
                print(f"[IER-KG] Neo4j connection failed: {e}")
                self.use_neo4j = False
    
    def extract_and_index_code(self, code: str, file_path: str, 
                               task_id: str) -> Tuple[List[CodeEntity], List[CodeRelation]]:
        """提取代码实体并索引"""
        # 提取实体和关系
        entities, relations = self.code_extractor.extract(code, file_path)
        
        # 保存到文件（或Neo4j）
        self._save_code_graph(entities, relations)
        
        # 同步到Neo4j（如果使用）
        if self.use_neo4j:
            self._sync_to_neo4j(entities, relations)
        
        return entities, relations
    
    def create_experience_with_provenance(self, exp_type: ExperienceEntityType,
                                         name: str, description: str, context: str,
                                         solution: str, code_example: Optional[str],
                                         task_id: str, file_path: str,
                                         source_code: str, tags: List[str] = None) -> Dict:
        """创建经验并建立溯源"""
        # 1. 提取代码实体
        entities, _ = self.extract_and_index_code(source_code, file_path, task_id)
        
        # 2. 创建经验节点
        exp = self.exp_manager.create_experience(
            exp_type=exp_type,
            name=name,
            description=description,
            context=context,
            solution=solution,
            code_example=code_example,
            tags=tags or []
        )
        
        # 3. 链接经验到代码实体
        for entity in entities[:3]:  # 关联前3个主要实体
            self.exp_manager.link_experience_to_code(exp.id, entity.id)
        
        # 4. 创建溯源链
        chain = self.provenance.create_provenance(
            experience_id=exp.id,
            task_id=task_id,
            file_path=file_path,
            code_entities=entities,
            source_code=source_code,
            extraction_method="ast+llm"
        )
        
        return {
            "experience": exp,
            "code_entities": entities,
            "provenance": chain
        }
    
    def retrieve_experiences(self, query: str, code_context: Optional[str] = None,
                            max_hops: int = 2, top_k: int = 10) -> List[Dict]:
        """检索经验（多跳）"""
        # 解析代码上下文（如果提供）
        code_entities = []
        if code_context:
            entities, _ = self.code_extractor.extract(code_context, "query_context.py")
            code_entities = entities
        
        # 多跳检索
        return self.retriever.retrieve(
            query_context=query,
            code_entities=code_entities,
            max_hops=max_hops,
            top_k=top_k
        )
    
    def get_experience_context(self, exp_id: str) -> Dict:
        """获取经验的完整上下文（包括关系、溯源）"""
        if exp_id not in self.exp_manager.experiences:
            return {"error": "Experience not found"}
        
        exp = self.exp_manager.experiences[exp_id]
        
        # 获取相关经验
        related = self.exp_manager.find_related_experiences(exp_id)
        
        # 获取溯源信息
        trace = self.provenance.trace_experience(exp_id)
        
        return {
            "experience": exp.to_dict(),
            "related_experiences": [
                {
                    "experience": rel[0].to_dict(),
                    "relation": rel[1].to_dict()
                }
                for rel in related
            ],
            "provenance": trace
        }
    
    def add_experience_relation(self, source_id: str, target_id: str,
                                relation_type: ExperienceRelationType,
                                strength: float = 1.0):
        """添加经验关系"""
        return self.exp_manager.add_relation(source_id, target_id, relation_type, strength)
    
    def get_statistics(self) -> Dict:
        """获取系统统计信息"""
        return {
            "code_entities": len(self.code_extractor.entities),
            "code_relations": len(self.code_extractor.relations),
            "experiences": len(self.exp_manager.experiences),
            "experience_edges": len(self.exp_manager.edges),
            "provenance_chains": len(self.provenance.chains),
            "neo4j_enabled": self.use_neo4j,
            "data_dir": str(IER_KG_DIR)
        }
    
    def export_for_visualization(self) -> Dict:
        """导出图谱数据用于可视化"""
        return {
            "nodes": [
                {"id": e.id, "label": e.name, "type": "experience", 
                 "category": e.exp_type.value}
                for e in self.exp_manager.experiences.values()
            ] + [
                {"id": e.id, "label": e.name, "type": "code_entity",
                 "category": e.entity_type.value}
                for e in self.code_extractor.entities
            ],
            "edges": [
                {"source": e.source_id, "target": e.target_id, 
                 "label": e.relation_type.value, "type": "experience_relation"}
                for e in self.exp_manager.edges.values()
            ] + [
                {"source": r.source_id, "target": r.target_id,
                 "label": r.relation_type.value, "type": "code_relation"}
                for r in self.code_extractor.relations
            ]
        }
    
    def _save_code_graph(self, entities: List[CodeEntity], relations: List[CodeRelation]):
        """保存代码图谱到文件"""
        data_file = IER_KG_DIR / 'code_graph.json'
        
        existing_data = {"entities": {}, "relations": {}}
        if data_file.exists():
            with open(data_file, 'r') as f:
                existing_data = json.load(f)
        
        # 合并新数据
        for e in entities:
            existing_data["entities"][e.id] = e.to_dict()
        for r in relations:
            existing_data["relations"][r.id] = r.to_dict()
        
        with open(data_file, 'w') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    def _sync_to_neo4j(self, entities: List[CodeEntity], relations: List[CodeRelation]):
        """同步到Neo4j"""
        if not self.neo4j_driver:
            return
        
        with self.neo4j_driver.session() as session:
            # 创建代码实体节点
            for entity in entities:
                session.run("""
                    MERGE (e:CodeEntity {id: $id})
                    SET e.name = $name,
                        e.entity_type = $entity_type,
                        e.file_path = $file_path,
                        e.line_start = $line_start,
                        e.line_end = $line_end,
                        e.signature = $signature
                """, **entity.to_dict())
            
            # 创建关系
            for relation in relations:
                session.run("""
                    MATCH (s:CodeEntity {id: $source_id})
                    MATCH (t:CodeEntity {id: $target_id})
                    MERGE (s)-[r:CODE_RELATION {type: $relation_type}]->(t)
                    SET r.context = $context
                """, **relation.to_dict())
    
    def close(self):
        """关闭资源"""
        if self.neo4j_driver:
            self.neo4j_driver.close()


# ==================== 便捷函数 ====================

def create_kg_system(use_neo4j: bool = False) -> IERKnowledgeGraphSystem:
    """创建知识图谱系统实例"""
    return IERKnowledgeGraphSystem(use_neo4j=use_neo4j)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("IER Knowledge Graph System - Test Mode")
    print("=" * 50)
    
    # 创建系统实例
    kg = create_kg_system(use_neo4j=False)
    
    # 测试代码提取
    test_code = '''
class DataProcessor:
    """数据处理类"""
    
    def __init__(self, config):
        self.config = config
        self.cache = {}
    
    @lru_cache(maxsize=128)
    def process(self, data):
        """处理数据"""
        return data.upper()
    
    def batch_process(self, items):
        """批量处理"""
        return [self.process(item) for item in items]
'''
    
    print("\n1. Extracting code entities...")
    entities, relations = kg.extract_and_index_code(test_code, "test_processor.py", "TEST_001")
    print(f"   Found {len(entities)} entities, {len(relations)} relations")
    
    for e in entities:
        print(f"   - {e.entity_type.value}: {e.name} (lines {e.line_start}-{e.line_end})")
    
    print("\n2. Creating experience with provenance...")
    result = kg.create_experience_with_provenance(
        exp_type=ExperienceEntityType.PATTERN,
        name="装饰器模式实现缓存",
        description="使用@lru_cache装饰器实现函数结果缓存",
        context="适用于需要缓存计算结果的场景",
        solution="使用functools.lru_cache装饰器，设置合适的maxsize",
        code_example="@lru_cache(maxsize=128)\ndef process(data): return data.upper()",
        task_id="TEST_001",
        file_path="test_processor.py",
        source_code=test_code,
        tags=["cache", "decorator", "performance"]
    )
    print(f"   Created experience: {result['experience'].id}")
    
    print("\n3. Retrieving experiences...")
    results = kg.retrieve_experiences("如何实现缓存", max_hops=2, top_k=5)
    print(f"   Found {len(results)} experiences")
    for r in results:
        print(f"   - {r['experience'].name} (hop={r['hop']}, score={r['relevance_score']:.2f})")
    
    print("\n4. System statistics...")
    stats = kg.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    kg.close()
    print("\n✓ Test completed")

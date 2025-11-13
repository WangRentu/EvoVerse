"""
学习记忆系统 - 存储成功模式、失败教训等
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import logging
import hashlib

logger = logging.getLogger(__name__)


class MemoryCategory(str, Enum):
    """记忆分类"""
    SUCCESS_PATTERNS = "success_patterns"
    FAILURE_PATTERNS = "failure_patterns"
    DEAD_ENDS = "dead_ends"
    INSIGHTS = "insights"
    GENERAL = "general"


class Memory(BaseModel):
    """单个记忆条目"""
    
    id: str
    category: MemoryCategory
    content: str
    data: Dict[str, Any] = Field(default_factory=dict)
    importance: float = Field(0.5, ge=0.0, le=1.0)
    access_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    
    def access(self):
        """记录记忆访问"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


class ExperimentSignature(BaseModel):
    """实验签名用于去重"""
    
    hypothesis_hash: str
    protocol_hash: str
    combined_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryStore:
    """
    学习记忆系统
    存储成功模式、失败模式等，避免重复错误
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        max_memories: int = 1000
    ):
        self.config = config or {}
        self.max_memories = max_memories
        
        # 按类别存储记忆
        self.memories: Dict[MemoryCategory, List[Memory]] = {
            category: [] for category in MemoryCategory
        }
        
        # 实验签名用于去重
        self.experiment_signatures: Dict[str, ExperimentSignature] = {}
        
        # 清理配置
        self.prune_after_days = self.config.get("prune_after_days", 30)
        self.min_importance_to_keep = self.config.get("min_importance_to_keep", 0.3)
        
        logger.info(f"MemoryStore initialized (max: {max_memories})")
    
    # ========================================================================
    # 记忆添加
    # ========================================================================
    
    def add_memory(
        self,
        category: MemoryCategory,
        content: str,
        importance: float = 0.5,
        data: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """添加记忆"""
        memory_id = hashlib.md5(f"{category}:{content}:{datetime.utcnow()}".encode()).hexdigest()[:16]
        
        memory = Memory(
            id=memory_id,
            category=category,
            content=content,
            importance=importance,
            data=data or {},
            tags=tags or []
        )
        
        self.memories[category].append(memory)
        
        # 清理过期记忆
        self._prune_memories()
        
        logger.debug(f"Added memory {memory_id} to {category}")
        return memory_id
    
    def add_success_pattern(self, pattern: str, success_rate: float = 1.0, tags: Optional[List[str]] = None) -> str:
        """添加成功模式"""
        return self.add_memory(
            MemoryCategory.SUCCESS_PATTERNS,
            pattern,
            importance=min(success_rate * 0.8, 0.9),  # 成功模式很重要
            data={"success_rate": success_rate},
            tags=tags or ["success"]
        )
    
    def add_failure_pattern(self, failure: str, lesson: str, tags: Optional[List[str]] = None) -> str:
        """添加失败模式"""
        return self.add_memory(
            MemoryCategory.FAILURE_PATTERNS,
            f"Failure: {failure}\nLesson: {lesson}",
            importance=0.7,  # 失败教训很重要
            data={"failure": failure, "lesson": lesson},
            tags=tags or ["failure"]
        )
    
    def add_dead_end(self, dead_end: str, reason: str, tags: Optional[List[str]] = None) -> str:
        """添加死胡同（要避免的）"""
        return self.add_memory(
            MemoryCategory.DEAD_ENDS,
            f"Dead End: {dead_end}\nReason: {reason}",
            importance=0.9,  # 死胡同非常重要，避免重复
            data={"dead_end": dead_end, "reason": reason},
            tags=tags or ["dead_end", "avoid"]
        )
    
    def add_insight(self, insight: str, source: str, related_items: Optional[List[str]] = None) -> str:
        """添加重要洞见"""
        return self.add_memory(
            MemoryCategory.INSIGHTS,
            insight,
            importance=0.95,  # 洞见非常重要
            data={"source": source, "related_items": related_items or []},
            tags=["insight", source]
        )
    
    # ========================================================================
    # 记忆查询
    # ========================================================================
    
    def query_memory(
        self,
        category: Optional[MemoryCategory] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[Memory]:
        """查询记忆"""
        results = []
        
        # 选择要搜索的类别
        if category:
            categories = [category]
        else:
            categories = list(MemoryCategory)
        
        # 搜索
        for cat in categories:
            for memory in self.memories[cat]:
                # 重要性过滤
                if memory.importance < min_importance:
                    continue
                
                # 标签过滤
                if tags and not any(tag in memory.tags for tag in tags):
                    continue
                
                results.append(memory)
        
        # 按重要性排序（考虑时间衰减）
        results.sort(
            key=lambda m: m.importance * (1.0 / max(1, (datetime.utcnow() - m.created_at).days + 1)),
            reverse=True
        )
        
        # 记录访问
        for memory in results[:limit]:
            memory.access()
        
        return results[:limit]
    
    def search_similar(self, query: str, category: Optional[MemoryCategory] = None, limit: int = 5) -> List[Memory]:
        """搜索相似记忆（简单关键词匹配）"""
        keywords = set(query.lower().split())
        
        similar = []
        
        categories = [category] if category else list(MemoryCategory)
        
        for cat in categories:
            for memory in self.memories[cat]:
                memory_keywords = set(memory.content.lower().split())
                overlap = len(keywords & memory_keywords)
                
                if overlap >= 2:  # 至少2个共同关键词
                    similar.append((memory, overlap))
        
        # 按重叠度排序
        similar.sort(key=lambda x: x[1], reverse=True)
        return [mem for mem, _ in similar[:limit]]
    
    # ========================================================================
    # 实验去重
    # ========================================================================
    
    def record_experiment(self, hypothesis: str, protocol: Optional[str] = None) -> str:
        """记录实验签名用于去重"""
        # 创建假设哈希
        hypothesis_hash = hashlib.md5(hypothesis.encode()).hexdigest()[:16]
        
        # 创建协议哈希
        if protocol:
            protocol_hash = hashlib.md5(protocol.encode()).hexdigest()[:16]
        else:
            protocol_hash = "none"
        
        # 组合哈希
        combined_hash = hashlib.md5(f"{hypothesis_hash}:{protocol_hash}".encode()).hexdigest()
        
        # 存储签名
        signature = ExperimentSignature(
            hypothesis_hash=hypothesis_hash,
            protocol_hash=protocol_hash,
            combined_hash=combined_hash
        )
        
        self.experiment_signatures[combined_hash] = signature
        
        return combined_hash
    
    def is_duplicate_experiment(self, hypothesis: str, protocol: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """检查是否是重复实验"""
        # 创建假设哈希
        hypothesis_hash = hashlib.md5(hypothesis.encode()).hexdigest()[:16]
        
        # 创建协议哈希
        if protocol:
            protocol_hash = hashlib.md5(protocol.encode()).hexdigest()[:16]
        else:
            protocol_hash = "none"
        
        # 组合哈希
        combined_hash = hashlib.md5(f"{hypothesis_hash}:{protocol_hash}".encode()).hexdigest()
        
        is_duplicate = combined_hash in self.experiment_signatures
        
        reason = f"Duplicate of experiment {combined_hash}" if is_duplicate else None
        
        return is_duplicate, reason
    
    # ========================================================================
    # 记忆管理
    # ========================================================================
    
    def _prune_memories(self):
        """清理过期和低重要性记忆"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.prune_after_days)
        
        for category in MemoryCategory:
            original_count = len(self.memories[category])
            
            # 保留重要记忆和近期记忆
            self.memories[category] = [
                memory for memory in self.memories[category]
                if (memory.importance >= self.min_importance_to_keep or 
                    memory.created_at > cutoff_date)
            ]
            
            pruned_count = original_count - len(self.memories[category])
            if pruned_count > 0:
                logger.debug(f"Pruned {pruned_count} memories from {category}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        total_memories = sum(len(memories) for memories in self.memories.values())
        
        return {
            "total_memories": total_memories,
            "by_category": {cat.value: len(memories) for cat, memories in self.memories.items()},
            "experiment_signatures": len(self.experiment_signatures),
            "max_memories": self.max_memories,
            "prune_after_days": self.prune_after_days
        }
    
    def clear_category(self, category: MemoryCategory):
        """清空特定类别的记忆"""
        self.memories[category] = []
        logger.info(f"Cleared all memories in category {category}")
    
    def clear_all(self):
        """清空所有记忆"""
        for category in MemoryCategory:
            self.memories[category] = []
        self.experiment_signatures = {}
        logger.info("Cleared all memories")
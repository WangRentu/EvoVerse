"""
EvoVerse 数据库模型和操作
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import logging

from evoverse.config import get_config

logger = logging.getLogger(__name__)

Base = declarative_base()

# 全局数据库连接
_engine = None
_SessionLocal = None


def init_database():
    """初始化数据库"""
    global _engine, _SessionLocal
    
    if _engine is not None:
        return
    
    cfg = get_config().db
    _engine = create_engine(cfg.url, echo=cfg.echo)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    # 创建所有表
    Base.metadata.create_all(bind=_engine)
    
    logger.info(f"Database initialized: {cfg.url}")


def get_session() -> Session:
    """获取数据库会话"""
    if _SessionLocal is None:
        init_database()
    
    return _SessionLocal()


class AgentRecord(Base):
    """
    Agent 记录 - 存储 Agent 状态和统计信息
    """
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    agent_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    
    # 配置
    config = Column(JSON, nullable=True)
    
    # 状态数据
    state_data = Column(JSON, nullable=True)
    
    # 统计信息
    messages_sent = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    errors_encountered = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Agent {self.agent_type} {self.id}>"


class ConversationRecord(Base):
    """
    对话记录 - 存储对话历史和元数据
    """
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=True)  # 关联的 Agent
    
    # 对话内容
    messages = Column(JSON, nullable=False)  # 消息历史
    
    # 元数据
    message_count = Column(Integer, default=0)
    max_history = Column(Integer, default=50)
    total_tokens = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    archived_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Conversation {self.session_id} ({self.message_count} messages)>"


class MemoryRecord(Base):
    """
    记忆记录 - 存储学习记忆和模式
    """
    __tablename__ = "memories"
    
    id = Column(String, primary_key=True)
    category = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    # 元数据
    importance = Column(Float, default=0.5)
    access_count = Column(Integer, default=0)
    tags = Column(JSON, nullable=True)  # 标签列表
    
    # 额外数据
    data = Column(JSON, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Memory {self.category} {self.id}>"


class TaskRecord(Base):
    """
    任务记录 - 存储任务执行历史
    """
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    
    # 任务内容
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    # 执行状态
    status = Column(String, default="pending")  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    
    # 性能指标
    execution_time = Column(Float, nullable=True)  # 秒
    tokens_used = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Task {self.task_type} {self.id} ({self.status})>"
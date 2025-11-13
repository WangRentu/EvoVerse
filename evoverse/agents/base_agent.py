"""
Agent 基类 - 提供状态管理和消息传递
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
from uuid import uuid4
import logging

from evoverse.db.relational import AgentRecord, get_session


logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Agent 状态"""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    WORKING = "working"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class MessageType(str, Enum):
    """消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    STATUS = "status"


class AgentMessage:
    """Agent 间消息"""
    
    def __init__(
        self,
        message_type: MessageType,
        from_agent: str,
        to_agent: str,
        content: Dict[str, Any],
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid4())
        self.type = message_type
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.content = content
        self.correlation_id = correlation_id
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class BaseAgent:
    """
    Agent 基类
    
    提供：
    - 生命周期管理
    - 状态持久化
    - 消息传递
    - 统计信息
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id or str(uuid4())
        self.agent_type = agent_type or self.__class__.__name__
        self.config = config or {}
        
        # 状态管理
        self.status = AgentStatus.CREATED
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # 消息处理
        self.message_queue: List[AgentMessage] = []
        self.message_handlers: Dict[str, Callable] = {}
        
        # 状态数据
        self.state_data: Dict[str, Any] = {}
        
        # 统计信息
        self.messages_received = 0
        self.messages_sent = 0
        self.tasks_completed = 0
        self.errors_encountered = 0
        
        logger.info(f"Agent {self.agent_type} ({self.agent_id}) created")
    
    # ========================================================================
    # 生命周期管理
    # ========================================================================
    
    def start(self):
        """启动 Agent"""
        if self.status != AgentStatus.CREATED:
            logger.warning(f"Agent {self.agent_id} already started")
            return
        
        self.status = AgentStatus.STARTING
        logger.info(f"Starting agent {self.agent_id}")
        
        try:
            self._on_start()
            self.status = AgentStatus.RUNNING
            logger.info(f"Agent {self.agent_id} started successfully")
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Failed to start agent {self.agent_id}: {e}")
            raise
    
    def stop(self):
        """停止 Agent"""
        logger.info(f"Stopping agent {self.agent_id}")
        
        try:
            self._on_stop()
            self.status = AgentStatus.STOPPED
            logger.info(f"Agent {self.agent_id} stopped")
        except Exception as e:
            logger.error(f"Error stopping agent {self.agent_id}: {e}")
            raise
    
    def pause(self):
        """暂停 Agent"""
        if self.status != AgentStatus.RUNNING:
            logger.warning(f"Cannot pause agent {self.agent_id} in status {self.status}")
            return
        
        self.status = AgentStatus.PAUSED
        logger.info(f"Agent {self.agent_id} paused")
    
    def resume(self):
        """恢复 Agent"""
        if self.status != AgentStatus.PAUSED:
            logger.warning(f"Cannot resume agent {self.agent_id} in status {self.status}")
            return
        
        self.status = AgentStatus.RUNNING
        logger.info(f"Agent {self.agent_id} resumed")
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.status == AgentStatus.RUNNING
    
    def is_healthy(self) -> bool:
        """健康检查"""
        return self.status in [AgentStatus.RUNNING, AgentStatus.IDLE, AgentStatus.WORKING]
    
    # ========================================================================
    # 状态持久化
    # ========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "is_healthy": self.is_healthy(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "statistics": {
                "messages_received": self.messages_received,
                "messages_sent": self.messages_sent,
                "tasks_completed": self.tasks_completed,
                "errors_encountered": self.errors_encountered,
            },
            "message_queue_length": len(self.message_queue),
        }
    
    def save_state(self):
        """保存状态到数据库"""
        try:
            with get_session() as session:
                # 检查是否已存在
                existing = session.query(AgentRecord).filter_by(id=self.agent_id).first()
                
                if existing:
                    # 更新现有记录
                    existing.status = self.status.value
                    existing.state_data = self.state_data
                    existing.messages_sent = self.messages_sent
                    existing.messages_received = self.messages_received
                    existing.tasks_completed = self.tasks_completed
                    existing.errors_encountered = self.errors_encountered
                    existing.updated_at = datetime.utcnow()
                else:
                    # 创建新记录
                    record = AgentRecord(
                        id=self.agent_id,
                        agent_type=self.agent_type,
                        status=self.status.value,
                        config=self.config,
                        state_data=self.state_data,
                        messages_sent=self.messages_sent,
                        messages_received=self.messages_received,
                        tasks_completed=self.tasks_completed,
                        errors_encountered=self.errors_encountered,
                    )
                    session.add(record)
                
                session.commit()
                logger.debug(f"Saved state for agent {self.agent_id}")
                
        except Exception as e:
            logger.error(f"Failed to save state for agent {self.agent_id}: {e}")
    
    def load_state(self):
        """从数据库加载状态"""
        try:
            with get_session() as session:
                record = session.query(AgentRecord).filter_by(id=self.agent_id).first()
                
                if record:
                    self.status = AgentStatus(record.status)
                    self.state_data = record.state_data or {}
                    self.messages_sent = record.messages_sent
                    self.messages_received = record.messages_received
                    self.tasks_completed = record.tasks_completed
                    self.errors_encountered = record.errors_encountered
                    self.created_at = record.created_at
                    self.updated_at = record.updated_at
                    
                    logger.debug(f"Loaded state for agent {self.agent_id}")
                    return True
                else:
                    logger.debug(f"No saved state found for agent {self.agent_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to load state for agent {self.agent_id}: {e}")
            return False
    
    def save_state_data(self, key: str, value: Any):
        """保存状态数据"""
        self.state_data[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_state_data(self, key: str, default: Any = None) -> Any:
        """获取状态数据"""
        return self.state_data.get(key, default)
    
    # ========================================================================
    # 消息传递
    # ========================================================================
    
    def send_message(
        self,
        to_agent: str,
        content: Dict[str, Any],
        message_type: MessageType = MessageType.REQUEST,
        correlation_id: Optional[str] = None
    ) -> AgentMessage:
        """发送消息"""
        message = AgentMessage(
            message_type=message_type,
            from_agent=self.agent_id,
            to_agent=to_agent,
            content=content,
            correlation_id=correlation_id
        )
        
        self.messages_sent += 1
        logger.debug(f"Agent {self.agent_id} sending {message_type.value} to {to_agent}")
        
        # 在实际实现中，这里会通过消息队列发送
        return message
    
    def receive_message(self, message: AgentMessage):
        """接收消息"""
        self.messages_received += 1
        self.message_queue.append(message)
        
        logger.debug(f"Agent {self.agent_id} received {message.type.value} from {message.from_agent}")
        
        # 处理消息
        try:
            self.process_message(message)
        except Exception as e:
            self.errors_encountered += 1
            logger.error(f"Error processing message in {self.agent_id}: {e}")
    
    def process_message(self, message: AgentMessage):
        """处理消息（子类重写）"""
        logger.warning(f"Agent {self.agent_id} received message but process_message() not implemented")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type} in agent {self.agent_id}")
    
    # ========================================================================
    # 执行接口
    # ========================================================================
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务（子类重写）"""
        raise NotImplementedError(f"execute() not implemented for {self.agent_type}")
    
    # ========================================================================
    # 生命周期钩子
    # ========================================================================
    
    def _on_start(self):
        """启动钩子"""
        pass
    
    def _on_stop(self):
        """停止钩子"""
        pass
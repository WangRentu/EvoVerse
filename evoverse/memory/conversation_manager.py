"""
对话管理器 - 处理多会话和对话历史
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

from evoverse.core.llm_client import ConversationMemory


class ConversationManager:
    """
    多会话对话管理器
    支持多个并发的对话会话
    """
    
    def __init__(self, storage_path: Optional[str] = None, max_sessions: int = 100):
        self.storage_path = Path(storage_path) if storage_path else Path(".conversations")
        self.storage_path.mkdir(exist_ok=True)
        self.max_sessions = max_sessions
        
        # 活跃会话
        self.active_sessions: Dict[str, ConversationMemory] = {}
        
        # 会话元数据
        self.session_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 从磁盘加载现有会话
        self._load_sessions()
    
    def create_session(self, session_id: Optional[str] = None, max_history: int = 50) -> str:
        """创建新会话"""
        if session_id is None:
            session_id = f"session_{int(datetime.now().timestamp())}"
        
        if session_id in self.active_sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        memory = ConversationMemory(max_history)
        self.active_sessions[session_id] = memory
        
        self.session_metadata[session_id] = {
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "message_count": 0,
            "max_history": max_history
        }
        
        # 清理旧会话
        self._cleanup_old_sessions()
        
        return session_id
    
    def get_session(self, session_id: str) -> ConversationMemory:
        """获取会话"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # 更新访问时间
        self.session_metadata[session_id]["last_accessed"] = datetime.now().isoformat()
        
        return self.active_sessions[session_id]
    
    def add_message(self, session_id: str, role: str, content: str):
        """向会话添加消息"""
        session = self.get_session(session_id)
        session.add_message(role, content)
        self.session_metadata[session_id]["message_count"] = len(session.messages)
    
    def get_messages(self, session_id: str, include_system: bool = True) -> List[Dict[str, str]]:
        """获取会话消息历史"""
        session = self.get_session(session_id)
        return session.get_messages(include_system)
    
    def save_session(self, session_id: str):
        """保存会话到磁盘"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        metadata = self.session_metadata[session_id]
        
        data = {
            "session_id": session_id,
            "metadata": metadata,
            "messages": session.messages,
            "created_at": session.created_at.isoformat(),
            "last_accessed": session.last_accessed.isoformat()
        }
        
        filepath = self.storage_path / f"{session_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_session(self, session_id: str) -> bool:
        """从磁盘加载会话"""
        filepath = self.storage_path / f"{session_id}.json"
        
        if not filepath.exists():
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 恢复会话记忆
            memory = ConversationMemory(data.get("max_history", 50))
            memory.messages = data["messages"]
            memory.created_at = datetime.fromisoformat(data["created_at"])
            memory.last_accessed = datetime.fromisoformat(data["last_accessed"])
            
            self.active_sessions[session_id] = memory
            self.session_metadata[session_id] = data["metadata"]
            
            return True
            
        except Exception as e:
            print(f"Failed to load session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            del self.session_metadata[session_id]
        
        # 删除磁盘文件
        filepath = self.storage_path / f"{session_id}.json"
        if filepath.exists():
            filepath.unlink()
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = []
        
        for session_id, metadata in self.session_metadata.items():
            sessions.append({
                "session_id": session_id,
                "created_at": metadata["created_at"],
                "last_accessed": metadata["last_accessed"],
                "message_count": metadata["message_count"],
                "max_history": metadata["max_history"]
            })
        
        # 按最后访问时间排序
        sessions.sort(key=lambda x: x["last_accessed"], reverse=True)
        
        return sessions
    
    def _load_sessions(self):
        """加载所有磁盘上的会话"""
        if not self.storage_path.exists():
            return
        
        for filepath in self.storage_path.glob("*.json"):
            session_id = filepath.stem
            self.load_session(session_id)
    
    def _cleanup_old_sessions(self):
        """清理旧会话"""
        if len(self.active_sessions) <= self.max_sessions:
            return
        
        # 按最后访问时间排序
        sorted_sessions = sorted(
            self.session_metadata.items(),
            key=lambda x: x[1]["last_accessed"]
        )
        
        # 删除最旧的会话
        to_delete = sorted_sessions[:len(sorted_sessions) - self.max_sessions + 1]
        
        for session_id, _ in to_delete:
            self.delete_session(session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_messages = sum(
            len(session.messages) 
            for session in self.active_sessions.values()
        )
        
        return {
            "active_sessions": len(self.active_sessions),
            "total_messages": total_messages,
            "max_sessions": self.max_sessions,
            "storage_path": str(self.storage_path)
        }
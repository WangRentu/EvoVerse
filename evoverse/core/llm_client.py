# evoverse/core/llm_client.py
from typing import List, Dict, Any, Optional
from openai import OpenAI
from datetime import datetime

from evoverse.config import get_config

class ConversationMemory:
    """对话记忆管理器"""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.messages: List[Dict[str, str]] = []
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
    
    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.messages.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        
        # 限制历史长度
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        self.last_accessed = datetime.now()
    
    def get_messages(self, include_system: bool = True) -> List[Dict[str, str]]:
        """获取消息历史（不包含时间戳）"""
        msgs = []
        for msg in self.messages:
            if not include_system and msg["role"] == "system":
                continue
            msgs.append({"role": msg["role"], "content": msg["content"]})
        return msgs
    
    def clear_history(self):
        """清空对话历史"""
        self.messages = []
        self.last_accessed = datetime.now()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "total_messages": len(self.messages),
            "max_history": self.max_history,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat()
        }


class LLMClient:
    """
    增强的 LLM 客户端，支持多轮对话记忆
    """
    
    def __init__(self, max_history: int = 50):
        cfg = get_config().llm
        self.model = cfg.model
        self.client = OpenAI(
            base_url=cfg.base_url,
            api_key=cfg.api_key,
        )
        self.temperature = cfg.temperature
        self.max_tokens = cfg.max_tokens
        
        # 对话记忆
        self.conversation_memory = ConversationMemory(max_history)
        
        # 统计信息
        self.total_requests = 0
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        发送消息到 LLM（兼容原有接口）
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        reply = resp.choices[0].message.content
        self.total_requests += 1
        
        return reply
    
    def chat_with_memory(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """
        带记忆的对话接口
        自动管理对话历史，支持连续对话
        """
        # 添加用户消息到记忆
        self.conversation_memory.add_message("user", user_message)
        
        # 构建完整消息历史
        messages = []
        
        # 添加系统提示（如果提供）
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息
        messages.extend(self.conversation_memory.get_messages(include_system=False))
        
        # 发送到 LLM
        reply = self.chat(messages)
        
        # 将回复添加到记忆
        self.conversation_memory.add_message("assistant", reply)
        
        return reply
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示（会覆盖之前的系统消息）"""
        # 移除旧的系统消息
        self.conversation_memory.messages = [
            msg for msg in self.conversation_memory.messages 
            if msg["role"] != "system"
        ]
        # 添加新的系统消息
        self.conversation_memory.add_message("system", prompt)
    
    def clear_memory(self):
        """清空对话记忆"""
        self.conversation_memory.clear_history()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        return {
            "conversation": self.conversation_memory.get_stats(),
            "total_requests": self.total_requests
        }
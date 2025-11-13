# evoverse/core/llm_client.py
from typing import List, Dict, Any
from openai import OpenAI

from evoverse.config import get_config


class LLMClient:
    """
    一个简单的 LLM 客户端封装：
    - 使用 OpenAI 官方 Python SDK
    - 但 base_url 指向 Ollama 的 OpenAI 兼容端点
    """

    def __init__(self):
        cfg = get_config().llm
        self.model = cfg.model
        self.client = OpenAI(
            base_url=cfg.base_url,
            api_key=cfg.api_key,  # Ollama 会忽略这个值，但 SDK 需要
        )
        self.temperature = cfg.temperature
        self.max_tokens = cfg.max_tokens

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        messages: [{"role": "user"/"system"/"assistant", "content": "..."}]
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return resp.choices[0].message.content
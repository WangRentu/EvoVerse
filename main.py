# main.py
from evoverse.core.llm_client import LLMClient
from evoverse.config import get_config


def main():
    cfg = get_config()
    print("EvoVerse starting with config:")
    print(f"  LLM base_url: {cfg.llm.base_url}")
    print(f"  LLM model   : {cfg.llm.model}")
    print(f"  DB url      : {cfg.db.url}")

    llm = LLMClient()

    user_question = "你是 EvoVerse 多智能体科研系统的内核大模型，请用两句话介绍一下你未来要完成的任务。"

    messages = [
        {"role": "system", "content": "你是一个科研助手大模型。"},
        {"role": "user", "content": user_question},
    ]

    print("\n>>> 向 LLM 发送测试问题...")
    reply = llm.chat(messages)
    print("\nLLM 回复：")
    print(reply)


if __name__ == "__main__":
    main()
# main.py
from evoverse.core.llm_client import LLMClient
from evoverse.config import get_config
from evoverse.memory import ConversationManager
from evoverse.agents import BaseAgent


def main():
    cfg = get_config()
    print("EvoVerse starting with config:")
    print(f"  LLM base_url: {cfg.llm.base_url}")
    print(f"  LLM model   : {cfg.llm.model}")
    print(f"  DB url      : {cfg.db.url}")

    # 创建带记忆的 LLM 客户端
    llm = LLMClient(max_history=20)
    
    # 创建对话管理器
    conversation_manager = ConversationManager()
    
    # 创建会话
    session_id = conversation_manager.create_session("demo_session")
    
    print(f"\n创建对话会话: {session_id}")
    
    # 设置系统提示
    system_prompt = "你是一个科研助手大模型，记住用户的偏好和之前的对话内容。"
    llm.set_system_prompt(system_prompt)
    
    # 演示连续对话
    questions = [
        "我是 EvoVerse 的开发者，专注于多智能体科研系统。",
        "你还记得我是谁吗？",
        "我最喜欢的编程语言是什么？",
        "请总结一下我们刚才的对话。"
    ]
    
    print("\n>>> 开始连续对话演示...")
    
    for i, question in enumerate(questions, 1):
        print(f"\n问题 {i}: {question}")
        
        # 使用记忆对话接口
        reply = llm.chat_with_memory(question)
        print(f"助手: {reply}")
        
        # 保存到对话管理器
        conversation_manager.add_message(session_id, "user", question)
        conversation_manager.add_message(session_id, "assistant", reply)
    
    # 显示记忆统计
    memory_stats = llm.get_memory_stats()
    print(f"\n记忆统计: {memory_stats}")
    
    # 保存会话
    conversation_manager.save_session(session_id)
    print(f"\n会话已保存: {session_id}")


if __name__ == "__main__":
    main()

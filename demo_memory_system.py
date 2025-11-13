#!/usr/bin/env python3
"""
EvoVerse 记忆系统演示
展示多层次记忆系统的完整功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from evoverse.config import get_config
from evoverse.core.llm_client import LLMClient
from evoverse.memory import MemoryStore, MemoryCategory, ConversationManager
from evoverse.agents import BaseAgent, AgentRegistry, MessageType
from evoverse.db.relational import init_database, get_session


def demo_conversation_memory():
    """演示对话记忆"""
    print("🔄 演示对话记忆系统")
    print("=" * 50)
    
    llm = LLMClient(max_history=10)
    
    # 设置系统提示
    llm.set_system_prompt("你是一个智能助手，记住用户的偏好和之前的对话内容。")
    
    # 第一次对话
    print("第一次对话:")
    response1 = llm.chat_with_memory("我喜欢蓝色，记住这个偏好。")
    print(f"助手: {response1}")
    
    # 第二次对话（测试记忆）
    print("\n第二次对话:")
    response2 = llm.chat_with_memory("我最喜欢的颜色是什么？")
    print(f"助手: {response2}")
    
    # 查看记忆统计
    stats = llm.get_memory_stats()
    print(f"\n记忆统计: {stats}")


def demo_learning_memory():
    """演示学习记忆"""
    print("\n🧠 演示学习记忆系统")
    print("=" * 50)
    
    memory_store = MemoryStore(max_memories=100)
    
    # 添加成功模式
    memory_store.add_success_pattern(
        "使用分治法解决复杂问题",
        success_rate=0.9,
        tags=["algorithm", "problem_solving"]
    )
    
    # 添加失败教训
    memory_store.add_failure_pattern(
        "尝试暴力枚举大数据集",
        "导致内存溢出和性能问题",
        tags=["performance", "mistake"]
    )
    
    # 添加重要洞见
    memory_store.add_insight(
        "神经网络的深度比宽度更重要",
        "literature_review",
        ["deep_learning", "architecture"]
    )
    
    # 查询记忆
    print("查询成功模式:")
    successes = memory_store.query_memory(MemoryCategory.SUCCESS_PATTERNS, limit=5)
    for mem in successes:
        print(f"  - {mem.content} (重要性: {mem.importance:.2f})")
    
    print("\n查询洞见:")
    insights = memory_store.query_memory(MemoryCategory.INSIGHTS, limit=5)
    for mem in insights:
        print(f"  - {mem.content}")
    
    # 记忆统计
    stats = memory_store.get_stats()
    print(f"\n记忆统计: {stats}")


def demo_agent_system():
    """演示 Agent 系统"""
    print("\n🤖 演示 Agent 系统")
    print("=" * 50)
    
    # 初始化数据库
    init_database()
    
    # 创建注册表
    registry = AgentRegistry()
    
    # 创建示例 Agent
    class DemoAgent(BaseAgent):
        def execute(self, task):
            return {"result": f"Processed task: {task}", "status": "success"}
    
    # 创建和注册 Agent
    agent1 = DemoAgent(agent_type="DemoAgent", config={"version": "1.0"})
    agent2 = DemoAgent(agent_type="WorkerAgent", config={"specialty": "computation"})
    
    registry.register(agent1)
    registry.register(agent2)
    
    # 显示注册表状态
    agents = registry.list_agents()
    print("注册的 Agent:")
    for agent in agents:
        print(f"  - {agent['agent_type']} ({agent['agent_id'][:8]}...) - {agent['status']}")
    
    # Agent 间通信
    message = agent1.send_message(
        to_agent=agent2.agent_id,
        content={"task": "compute_fibonacci", "n": 10},
        message_type=MessageType.REQUEST
    )
    
    # 路由消息
    registry.route_message(message)
    
    # 保存状态
    agent1.save_state()
    
    print("\nAgent 状态已保存到数据库")
    
    # 显示统计
    stats = registry.get_stats()
    print(f"注册表统计: {stats}")


def demo_conversation_manager():
    """演示对话管理器"""
    print("\n💬 演示对话管理器")
    print("=" * 50)
    
    manager = ConversationManager(max_sessions=10)
    
    # 创建会话
    session_id = manager.create_session(max_history=5)
    print(f"创建会话: {session_id}")
    
    # 添加消息
    manager.add_message(session_id, "user", "你好")
    manager.add_message(session_id, "assistant", "你好！很高兴见到你。")
    manager.add_message(session_id, "user", "今天天气怎么样？")
    
    # 获取消息历史
    messages = manager.get_messages(session_id)
    print("对话历史:")
    for msg in messages:
        print(f"  {msg['role']}: {msg['content']}")
    
    # 保存会话
    manager.save_session(session_id)
    print(f"\n会话已保存: {session_id}")
    
    # 列出会话
    sessions = manager.list_sessions()
    print("所有会话:")
    for session in sessions[:3]:  # 只显示前3个
        print(f"  - {session['session_id']}: {session['message_count']} 条消息")


def main():
    """主演示函数"""
    print("🚀 EvoVerse 多层次记忆系统演示")
    print("=" * 60)
    
    try:
        # 显示配置
        cfg = get_config()
        print("配置信息:")
        print(f"  LLM: {cfg.llm.model} @ {cfg.llm.base_url}")
        print(f"  DB: {cfg.db.url}")
        print(f"  Memory: max_memories={cfg.memory.max_memories}")
        print()
        
        # 运行演示
        demo_conversation_memory()
        demo_learning_memory()
        demo_agent_system()
        demo_conversation_manager()
        
        print("\n✅ 所有演示完成！")
        print("\nEvoVerse 记忆系统特性:")
        print("- 🔄 对话记忆：自动管理多轮对话历史")
        print("- 🧠 学习记忆：存储成功模式、失败教训和洞见")
        print("- 🤖 Agent 状态：持久化 Agent 状态和统计信息")
        print("- 💬 多会话管理：支持并发对话会话")
        print("- 💾 数据库存储：结构化数据持久化")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
EvoVerse Gradio 可视化框架
展示问答、记忆、管理系统的完整功能
"""

import sys
from pathlib import Path
import json
import gradio as gr
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from evoverse.config import get_config
from evoverse.core.llm_client import LLMClient
from evoverse.memory import MemoryStore, MemoryCategory, ConversationManager
from evoverse.agents import BaseAgent, AgentRegistry, MessageType
from evoverse.db.relational import init_database, get_session, AgentRecord, MemoryRecord, ConversationRecord, TaskRecord


# 全局实例
llm_client = None
memory_store = None
conversation_manager = None
agent_registry = None


def initialize_system():
    """初始化 EvoVerse 系统"""
    global llm_client, memory_store, conversation_manager, agent_registry
    
    if llm_client is None:
        # 初始化配置
        cfg = get_config()
        
        # 初始化 LLM 客户端
        llm_client = LLMClient(max_history=20)
        
        # 初始化记忆系统
        memory_store = MemoryStore(max_memories=cfg.memory.max_memories)
        
        # 初始化对话管理器
        conversation_manager = ConversationManager()
        
        # 初始化数据库
        init_database()
        
        # 初始化 Agent 注册表
        agent_registry = AgentRegistry()
        
        print("✅ EvoVerse 系统初始化完成")


# =============================================================================
# 问答界面功能
# =============================================================================

def extract_session_id(formatted_session: str) -> str:
    """从格式化的会话字符串中提取纯 session_id"""
    if not formatted_session or formatted_session == "无活跃会话":
        return ""
    
    # 从 "session_1763026852 (0 条消息)" 中提取 "session_1763026852"
    if " (" in formatted_session and formatted_session.endswith(")"):
        return formatted_session.split(" (")[0]
    
    return formatted_session


def chat_with_llm(message: str, formatted_session: str, system_prompt: str = "") -> str:
    """与 LLM 对话"""
    global llm_client, conversation_manager
    
    if not llm_client:
        return "❌ 系统未初始化"
    
    # 从格式化字符串中提取纯 session_id
    session_id = extract_session_id(formatted_session)
    if not session_id:
        return "❌ 无效的会话 ID"
    
    try:
        # 设置系统提示
        if system_prompt and system_prompt != llm_client.conversation_memory.messages[0]["content"] if llm_client.conversation_memory.messages else "":
            llm_client.set_system_prompt(system_prompt)
        
        # 对话
        response = llm_client.chat_with_memory(message)
        
        # 保存到会话管理器
        conversation_manager.add_message(session_id, "user", message)
        conversation_manager.add_message(session_id, "assistant", response)
        conversation_manager.save_session(session_id)
        
        return response
    
    except Exception as e:
        return f"❌ 对话失败: {str(e)}"


def clear_chat_history(formatted_session: str) -> str:
    """清空对话历史"""
    global llm_client, conversation_manager
    
    session_id = extract_session_id(formatted_session)
    if not session_id:
        return "❌ 无效的会话 ID"
    
    if llm_client:
        llm_client.clear_memory()
    
    if conversation_manager and session_id in conversation_manager.active_sessions:
        conversation_manager.delete_session(session_id)
    
    return "🧹 对话历史已清空"


def create_new_session() -> str:
    """创建新会话"""
    global conversation_manager
    
    if conversation_manager:
        session_id = conversation_manager.create_session()
        return f"✅ 新会话创建: {session_id}"
    
    return "❌ 会话管理器未初始化"


def get_session_list() -> List[str]:
    """获取会话列表"""
    global conversation_manager
    
    if conversation_manager:
        sessions = conversation_manager.list_sessions()
        return [f"{s['session_id']} ({s['message_count']} 条消息)" for s in sessions]
    
    return ["无活跃会话"]


# =============================================================================
# 记忆可视化功能
# =============================================================================

def get_memory_stats() -> Dict[str, Any]:
    """获取记忆统计"""
    global memory_store, llm_client, conversation_manager
    
    stats = {
        "学习记忆": memory_store.get_stats() if memory_store else {"error": "未初始化"},
        "对话记忆": llm_client.get_memory_stats() if llm_client else {"error": "未初始化"},
        "会话管理": conversation_manager.get_stats() if conversation_manager else {"error": "未初始化"}
    }
    
    return stats


def get_memory_dataframe(category_filter: str = "all") -> pd.DataFrame:
    """获取记忆数据表格"""
    global memory_store
    
    if not memory_store:
        return pd.DataFrame()
    
    memories = []
    categories = [MemoryCategory.SUCCESS_PATTERNS, MemoryCategory.FAILURE_PATTERNS, 
                 MemoryCategory.DEAD_ENDS, MemoryCategory.INSIGHTS, MemoryCategory.GENERAL]
    
    if category_filter != "all":
        categories = [MemoryCategory(category_filter)]
    
    for category in categories:
        category_memories = memory_store.memories.get(category, [])
        for mem in category_memories:
            memories.append({
                "ID": mem.id[:8] + "...",
                "分类": mem.category.value,
                "内容": mem.content[:50] + "..." if len(mem.content) > 50 else mem.content,
                "重要性": f"{mem.importance:.2f}",
                "访问次数": mem.access_count,
                "标签": ", ".join(mem.tags),
                "创建时间": mem.created_at.strftime("%Y-%m-%d %H:%M"),
                "最后访问": mem.last_accessed.strftime("%Y-%m-%d %H:%M")
            })
    
    return pd.DataFrame(memories)


def add_learning_memory(category: str, content: str, importance: float, tags: str) -> str:
    """添加学习记忆"""
    global memory_store
    
    if not memory_store:
        return "❌ 记忆系统未初始化"
    
    try:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        if category == "success_patterns":
            memory_id = memory_store.add_success_pattern(content, importance, tag_list)
        elif category == "failure_patterns":
            memory_id = memory_store.add_failure_pattern(content, "学习教训", tag_list)
        elif category == "insights":
            memory_id = memory_store.add_insight(content, "manual_input", tag_list)
        else:
            memory_id = memory_store.add_memory(MemoryCategory(category), content, importance, tags=tag_list)
        
        return f"✅ 记忆已添加 (ID: {memory_id[:8]}...)"
    
    except Exception as e:
        return f"❌ 添加失败: {str(e)}"


# =============================================================================
# Agent 管理功能
# =============================================================================

def get_agent_dataframe() -> pd.DataFrame:
    """获取 Agent 数据表格"""
    try:
        with get_session() as session:
            agents = session.query(AgentRecord).all()
            
            agent_data = []
            for agent in agents:
                agent_data.append({
                    "ID": agent.id,
                    "类型": agent.agent_type,
                    "状态": agent.status,
                    "发送消息": agent.messages_sent,
                    "接收消息": agent.messages_received,
                    "完成任务": agent.tasks_completed,
                    "错误次数": agent.errors_encountered,
                    "创建时间": agent.created_at.strftime("%Y-%m-%d %H:%M"),
                    "更新时间": agent.updated_at.strftime("%Y-%m-%d %H:%M")
                })
            
            return pd.DataFrame(agent_data)
    
    except Exception as e:
        return pd.DataFrame({"错误": [f"数据库查询失败: {str(e)}"]})


def create_demo_agent(agent_type: str, agent_id: str) -> str:
    """创建演示 Agent"""
    global agent_registry
    
    if not agent_registry:
        return "❌ Agent 注册表未初始化"
    
    try:
        # 创建 Agent
        agent = BaseAgent(agent_id=agent_id, agent_type=agent_type)
        agent_registry.register(agent)
        
        # 保存到数据库
        agent.save_state()
        
        return f"✅ Agent 创建成功: {agent_type} ({agent_id})"
    
    except Exception as e:
        return f"❌ 创建失败: {str(e)}"


# =============================================================================
# 会话管理功能
# =============================================================================

def get_conversation_dataframe() -> pd.DataFrame:
    """获取对话数据表格"""
    try:
        with get_session() as session:
            conversations = session.query(ConversationRecord).all()
            
            conv_data = []
            for conv in conversations:
                conv_data.append({
                    "会话ID": conv.id,
                    "消息数": conv.message_count,
                    "最大历史": conv.max_history,
                    "Agent ID": conv.agent_id or "无",
                    "创建时间": conv.created_at.strftime("%Y-%m-%d %H:%M"),
                    "最后访问": conv.last_accessed.strftime("%Y-%m-%d %H:%M")
                })
            
            return pd.DataFrame(conv_data)
    
    except Exception as e:
        return pd.DataFrame({"错误": [f"数据库查询失败: {str(e)}"]})


def get_session_messages(session_id: str) -> str:
    """获取会话消息"""
    global conversation_manager
    
    if not conversation_manager:
        return "❌ 会话管理器未初始化"
    
    try:
        messages = conversation_manager.get_messages(session_id)
        
        if not messages:
            return "📭 该会话没有消息"
        
        formatted = []
        for msg in messages[-10:]:  # 只显示最近10条
            role_emoji = "👤" if msg["role"] == "user" else "🤖"
            formatted.append(f"{role_emoji} **{msg['role']}**: {msg['content']}")
        
        return "\n\n".join(formatted)
    
    except Exception as e:
        return f"❌ 获取失败: {str(e)}"


# =============================================================================
# 统计面板功能
# =============================================================================

def create_memory_chart() -> go.Figure:
    """创建记忆分布图表"""
    global memory_store
    
    if not memory_store:
        return go.Figure()
    
    stats = memory_store.get_stats()
    categories = list(stats["by_category"].keys())
    counts = list(stats["by_category"].values())
    
    fig = px.bar(
        x=categories, 
        y=counts,
        title="学习记忆分类分布",
        labels={"x": "记忆分类", "y": "条目数量"}
    )
    
    return fig


def get_system_stats() -> Dict[str, Any]:
    """获取系统统计信息"""
    try:
        with get_session() as session:
            agent_count = session.query(AgentRecord).count()
            memory_count = session.query(MemoryRecord).count()
            conversation_count = session.query(ConversationRecord).count()
            task_count = session.query(TaskRecord).count()
        
        stats = {
            "数据库统计": {
                "Agent 数量": agent_count,
                "学习记忆条数": memory_count,
                "对话记录数": conversation_count,
                "任务记录数": task_count
            },
            "系统状态": {
                "LLM 客户端": "已初始化" if llm_client else "未初始化",
                "记忆系统": "已初始化" if memory_store else "未初始化",
                "会话管理器": "已初始化" if conversation_manager else "未初始化",
                "Agent 注册表": "已初始化" if agent_registry else "未初始化"
            }
        }
        
        return stats
    
    except Exception as e:
        return {"错误": f"获取统计失败: {str(e)}"}


# =============================================================================
# Gradio 界面构建
# =============================================================================

def create_gradio_interface():
    """创建 Gradio 界面"""
    
    # 初始化系统
    initialize_system()
    
    with gr.Blocks(title="EvoVerse 可视化框架", theme=gr.themes.Soft()) as demo:
        
        gr.Markdown("""
        # 🚀 EvoVerse 多层次记忆系统可视化框架
        
        一个完整的 AI Agent 记忆管理系统，支持对话、学习记忆、Agent 管理和会话控制。
        
        ## ✨ 功能特性
        💬 **智能对话**: 支持多轮连续对话和上下文记忆 ｜ 🧠 **学习记忆**: 记录成功模式、失败教训和重要洞见 ｜ 🤖 **Agent 管理**: 可视化 Agent 状态和通信统计 ｜ 📊 **会话控制**: 管理多个对话会话和历史记录 ｜ 📈 **统计面板**: 系统运行状态和性能监控
        """)
        
        with gr.Tabs():
            
            # ========================================
            # 问答界面
            # ========================================
            with gr.TabItem("💬 智能问答", id="chat"):
                gr.Markdown("### 🤖 与 EvoVerse 进行智能对话")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        session_selector = gr.Dropdown(
                            choices=get_session_list(),
                            value=get_session_list()[0] if get_session_list() else None,
                            label="选择会话",
                            info="选择或创建对话会话"
                        )
                        new_session_btn = gr.Button("🆕 创建新会话", variant="secondary")
                        
                        system_prompt = gr.Textbox(
                            label="系统提示",
                            placeholder="输入系统角色设定...",
                            lines=3,
                            value="你是一个智能科研助手，能够记住对话历史并提供有帮助的回答。请记住用户的偏好和之前的讨论内容。"
                        )
                        
                        clear_btn = gr.Button("🧹 清空历史", variant="stop")
                    
                    with gr.Column(scale=2):
                        # 修复：添加 type='messages' 参数
                        chatbot = gr.Chatbot(
                            height=400,
                            show_label=False,
                            container=True,
                            type='messages'  # ✅ 修复：添加消息格式参数
                        )
                        
                        msg = gr.Textbox(
                            label="输入您的问题",
                            placeholder="在这里输入您的问题...",
                            lines=2
                        )
                        
                        with gr.Row():
                            submit_btn = gr.Button("发送", variant="primary", scale=2)
                            retry_btn = gr.Button("重试", scale=1)
                            undo_btn = gr.Button("撤销", scale=1)
                
                # 问答界面事件
                def respond(message, chat_history, formatted_session):
                    if not message.strip():
                        return "", chat_history
                    
                    # 验证会话 ID
                    session_id = extract_session_id(formatted_session)
                    if not session_id:
                        error_msg = "❌ 请先选择或创建一个有效的会话"
                        return "", chat_history + [{"role": "assistant", "content": error_msg}]
                    
                    # 构建消息格式
                    messages = []
                    if chat_history:
                        messages.extend(chat_history)
                    
                    # 添加新消息
                    messages.append({"role": "user", "content": message})
                    
                    # 获取 AI 回复
                    bot_message = chat_with_llm(message, formatted_session, system_prompt.value)
                    
                    # 添加 AI 回复
                    messages.append({"role": "assistant", "content": bot_message})
                    
                    return "", messages
                
                msg.submit(respond, [msg, chatbot, session_selector], [msg, chatbot])
                submit_btn.click(respond, [msg, chatbot, session_selector], [msg, chatbot])
                
                new_session_btn.click(
                    lambda: (create_new_session(), gr.update(choices=get_session_list())),
                    outputs=[gr.Textbox(visible=False), session_selector]
                ).then(
                    lambda: None,
                    outputs=chatbot
                )
                
                clear_btn.click(
                    lambda formatted_session: (clear_chat_history(formatted_session), None),
                    inputs=session_selector,
                    outputs=[gr.Textbox(visible=False), chatbot]
                )
            
            # ========================================
            # 记忆可视化
            # ========================================
            with gr.TabItem("🧠 记忆可视化", id="memory"):
                gr.Markdown("### 📚 学习记忆系统可视化")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 📊 记忆统计")
                        memory_stats_display = gr.JSON(
                            value=get_memory_stats(),
                            label="记忆系统状态"
                        )
                        refresh_stats_btn = gr.Button("🔄 刷新统计")
                    
                    with gr.Column():
                        gr.Markdown("#### 📈 记忆分布图")
                        memory_chart = gr.Plot(value=create_memory_chart())
                
                gr.Markdown("#### 📋 记忆条目列表")
                
                with gr.Row():
                    category_filter = gr.Dropdown(
                        choices=["all", "success_patterns", "failure_patterns", "dead_ends", "insights", "general"],
                        value="all",
                        label="记忆分类过滤"
                    )
                    search_btn = gr.Button("🔍 搜索")
                
                # 修复：移除 height 参数
                memory_table = gr.DataFrame(
                    value=get_memory_dataframe(),
                    label="学习记忆条目"
                )
                
                gr.Markdown("#### ➕ 添加新记忆")
                
                with gr.Row():
                    with gr.Column():
                        memory_category = gr.Dropdown(
                            choices=["success_patterns", "failure_patterns", "insights", "general"],
                            label="记忆分类"
                        )
                        memory_content = gr.Textbox(
                            label="记忆内容",
                            placeholder="输入记忆内容...",
                            lines=3
                        )
                    
                    with gr.Column():
                        memory_importance = gr.Slider(
                            minimum=0.0, maximum=1.0, value=0.7, step=0.1,
                            label="重要性"
                        )
                        memory_tags = gr.Textbox(
                            label="标签",
                            placeholder="用逗号分隔多个标签...",
                            value=""
                        )
                        add_memory_btn = gr.Button("✅ 添加记忆", variant="primary")
                
                add_result = gr.Textbox(label="操作结果", interactive=False)
                
                # 记忆可视化事件
                refresh_stats_btn.click(
                    lambda: get_memory_stats(),
                    outputs=memory_stats_display
                ).then(
                    lambda: create_memory_chart(),
                    outputs=memory_chart
                )
                
                search_btn.click(
                    lambda cat: get_memory_dataframe(cat),
                    inputs=category_filter,
                    outputs=memory_table
                )
                
                add_memory_btn.click(
                    add_learning_memory,
                    inputs=[memory_category, memory_content, memory_importance, memory_tags],
                    outputs=add_result
                ).then(
                    lambda cat: get_memory_dataframe(cat),
                    inputs=category_filter,
                    outputs=memory_table
                )
            
            # ========================================
            # Agent 管理
            # ========================================
            with gr.TabItem("🤖 Agent 管理", id="agents"):
                gr.Markdown("### 🎭 Agent 管理系统")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 📋 Agent 列表")
                        # 修复：移除 height 参数
                        agent_table = gr.DataFrame(
                            value=get_agent_dataframe(),
                            label="活跃 Agent"
                        )
                        refresh_agents_btn = gr.Button("🔄 刷新列表")
                    
                    with gr.Column():
                        gr.Markdown("#### 🆕 创建新 Agent")
                        agent_type = gr.Textbox(
                            label="Agent 类型",
                            placeholder="例如: ResearchAgent, ChatAgent",
                            value="DemoAgent"
                        )
                        agent_id = gr.Textbox(
                            label="Agent ID",
                            placeholder="例如: agent_001",
                            value=f"agent_{int(datetime.now().timestamp())}"
                        )
                        create_agent_btn = gr.Button("🚀 创建 Agent", variant="primary")
                        create_result = gr.Textbox(label="创建结果", interactive=False)
                
                # Agent 管理事件
                refresh_agents_btn.click(
                    get_agent_dataframe,
                    outputs=agent_table
                )
                
                create_agent_btn.click(
                    create_demo_agent,
                    inputs=[agent_type, agent_id],
                    outputs=create_result
                ).then(
                    get_agent_dataframe,
                    outputs=agent_table
                )
            
            # ========================================
            # 会话管理
            # ========================================
            with gr.TabItem("💬 会话管理", id="sessions"):
                gr.Markdown("### 📝 对话会话管理")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 📋 会话列表")
                        # 修复：移除 height 参数
                        session_table = gr.DataFrame(
                            value=get_conversation_dataframe(),
                            label="对话会话"
                        )
                        refresh_sessions_btn = gr.Button("🔄 刷新列表")
                    
                    with gr.Column():
                        gr.Markdown("#### 💬 会话详情")
                        session_id_input = gr.Textbox(
                            label="会话 ID",
                            placeholder="输入会话 ID 查看详情"
                        )
                        view_session_btn = gr.Button("👀 查看消息")
                        session_messages = gr.Markdown(
                            value="选择一个会话 ID 查看消息历史",
                            label="消息历史"
                        )
                
                # 会话管理事件
                refresh_sessions_btn.click(
                    get_conversation_dataframe,
                    outputs=session_table
                )
                
                view_session_btn.click(
                    get_session_messages,
                    inputs=session_id_input,
                    outputs=session_messages
                )
            
            # ========================================
            # 统计面板
            # ========================================
            with gr.TabItem("📊 统计面板", id="stats"):
                gr.Markdown("### 📈 系统统计与监控")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 🔢 系统概览")
                        system_stats = gr.JSON(
                            value=get_system_stats(),
                            label="系统统计信息"
                        )
                        refresh_system_btn = gr.Button("🔄 刷新统计")
                    
                    with gr.Column():
                        gr.Markdown("#### 📊 记忆分布")
                        memory_dist_chart = gr.Plot(value=create_memory_chart())
                
                gr.Markdown("#### 📋 数据库表详情")
                
                with gr.Tabs():
                    with gr.TabItem("Agent 表"):
                        # 修复：移除 height 参数
                        agent_stats_table = gr.DataFrame(
                            value=get_agent_dataframe()
                        )
                    
                    with gr.TabItem("记忆表"):
                        # 修复：移除 height 参数
                        memory_stats_table = gr.DataFrame(
                            value=get_memory_dataframe()
                        )
                    
                    with gr.TabItem("会话表"):
                        # 修复：移除 height 参数
                        conversation_stats_table = gr.DataFrame(
                            value=get_conversation_dataframe()
                        )
                
                # 统计面板事件
                refresh_system_btn.click(
                    get_system_stats,
                    outputs=system_stats
                ).then(
                    lambda: create_memory_chart(),
                    outputs=memory_dist_chart
                )
    
    return demo


# =============================================================================
# 主函数
# =============================================================================

if __name__ == "__main__":
    # 创建并启动 Gradio 应用
    demo = create_gradio_interface()
    
    print("🚀 启动 EvoVerse 可视化框架...")
    print("📱 访问 http://localhost:7860 查看界面")
    
    # 启动应用
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

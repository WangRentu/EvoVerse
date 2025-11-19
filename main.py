"""
EvoVerse MVP CLI

提供一个最小可行的命令行入口：
- 从标准输入读取科研问题
- 调用 ResearchDirectorAgent 执行完整流水线
- 在控制台打印结构化结果摘要
""" 
from __future__ import annotations

import json
from typing import Any, Dict

from evoverse.db.relational import init_database
from evoverse.agents.research_director import ResearchDirectorAgent

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),                     # 打到终端
        logging.FileHandler("evoverse.log", encoding="utf-8"),  # 写到文件
    ],
)

def run_cli() -> None:
    """简单的命令行交互入口。"""
    init_database()

    print("🔬 EvoVerse MVP - ResearchDirector CLI")
    print("请输入一个科研问题（按回车确认，空行退出）：")

    try:
        # question = input("> ").strip()
        question = "智能群体演化和基因科学的研究"
        print(f"> {question}")
    except EOFError:
        return

    if not question:
        print("未输入问题，退出。")
        return

    director = ResearchDirectorAgent()
    result: Dict[str, Any] = director.run_task(question)

    print("\n=== 任务摘要 ===")
    print(f"Task ID: {result.get('task_id')}")
    print(f"问题：{result.get('question')}")

    print("\n子问题：")
    for i, sq in enumerate(result.get("sub_questions", []), start=1):
        print(f"  {i}. {sq}")

    print("\n关键词：", ", ".join(result.get("keywords", [])))

    papers = result.get("papers", [])
    print(f"\n检索到的文献数量：{len(papers)}")
    for i, p in enumerate(papers[:5], start=1):
        print(f"  [{i}] {p.get('title', '')}")

    print("\n知识图谱增量：")
    print(json.dumps(result.get("graph_stats", {}), ensure_ascii=False, indent=2))

    print("\n候选假设与方案（JSON 摘要）：")
    summary_obj = {
        "hypotheses": result.get("hypotheses", []),
        "plan": result.get("plan", []),
    }
    print(json.dumps(summary_obj, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run_cli()


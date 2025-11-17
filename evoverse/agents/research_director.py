"""
ResearchDirectorAgent - MVP 版本科研调度 Agent

负责将用户提出的科研问题串联起一个最小可行流水线：
- 问题理解与子问题拆解
- 文献检索
- 知识图谱增量构建
- 假设与研究方案草拟
- 任务执行记录落盘
"""

from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime
import logging
import re

from evoverse.agents.base_agent import BaseAgent
from evoverse.core.llm_client import LLMClient
from evoverse.db.relational import TaskRecord, get_session

from .research_literature_agent import LiteratureAgent
from .research_knowledge_agent import KnowledgeAgent


logger = logging.getLogger(__name__)


class ResearchDirectorAgent(BaseAgent):
    """
    MVP 版本的 Research Director

    设计目标：
    - 提供一个从「问题输入 → 文献 → 知识图 → LLM 推理 → 结果落盘」的纵向闭环
    - 不追求复杂多智能体消息路由，以内联函数调用为主，后续可以平滑升级
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        llm_client: Optional[LLMClient] = None,
        literature_agent: Optional[LiteratureAgent] = None,
        knowledge_agent: Optional[KnowledgeAgent] = None,
    ):
        super().__init__(agent_id=agent_id, agent_type="ResearchDirector", config=config)
        self.llm = llm_client or LLMClient(max_history=32)
        self.literature_agent = literature_agent or LiteratureAgent()
        self.knowledge_agent = knowledge_agent or KnowledgeAgent()

    # ---------------------------------------------------------------------
    # 对外主入口
    # ---------------------------------------------------------------------

    def run_task(self, question: str) -> Dict[str, Any]:
        """
        执行一次端到端科研回合（同步阻塞调用）。

        返回结构化结果：
        {
            "task_id": ...,
            "question": ...,
            "sub_questions": [...],
            "keywords": [...],
            "papers": [...],          # 精简后的文献信息
            "graph_stats": {...},     # 图谱增量统计
            "hypotheses": [...],      # 假设与推理链
            "plan": [...],            # 初步研究方案
            "created_at": ...
        }
        """
        self.status = self.status.WORKING
        self.save_state()

        task_id = str(uuid4())
        task_record = self._create_task_record(task_id, question)

        try:
            # 1. 问题理解与子问题拆解
            planning = self._plan_research(question)

            # 2. 文献检索
            papers = self.literature_agent.search_and_summarize(
                query="; ".join(planning["keywords"]) or question,
                max_results=planning.get("max_papers", 20),
            )

            # 3. 写入知识图谱
            graph_stats = self.knowledge_agent.ingest_papers(papers)

            # 4. 基于「问题 + 文献摘要 + 图谱增量信息」生成假设与方案
            reasoning = self._synthesize_hypotheses(
                question=question,
                planning=planning,
                papers=papers,
                graph_stats=graph_stats,
            )

            result: Dict[str, Any] = {
                "task_id": task_id,
                "question": question,
                "sub_questions": planning["sub_questions"],
                "keywords": planning["keywords"],
                "papers": papers,
                "graph_stats": graph_stats,
                "hypotheses": reasoning["hypotheses"],
                "plan": reasoning["plan"],
                "created_at": datetime.utcnow().isoformat(),
            }

            # 更新任务记录
            self._complete_task_record(task_record, result)
            self.tasks_completed += 1
            self.status = self.status.IDLE
            self.save_state()

            return result

        except Exception as exc:  # noqa: BLE001
            logger.error("ResearchDirectorAgent run_task failed: %s", exc)
            self.errors_encountered += 1
            self.status = self.status.ERROR
            self.save_state()
            self._fail_task_record(task_record, str(exc))
            raise

    # ------------------------------------------------------------------
    # 内部步骤：规划 / 综合
    # ------------------------------------------------------------------

    def _plan_research(self, question: str) -> Dict[str, Any]:
        """使用 LLM 做粗粒度任务拆解，生成子问题与检索关键词。"""
        system_prompt = (
            "You are a research planning assistant. Given a scientific research question, "
            "first translate the question into English if it is not already in English. "
            "Then output a JSON object containing: sub_questions (3–5 items), "
            "keywords (5–10 items), and max_papers (an integer, recommended between 10–30). "
            "All sub_questions and keywords must be in English."
        )

        user_prompt = (
            "The research question is as follows:\n"
            f"{question}\n\n"
            "Please output JSON directly in ```json``` format, without comments or any additional text."
        )

        raw = self.llm.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        # print(raw)

        import json

        # 统一拿到字符串形式的内容   
        raw_text = raw if isinstance(raw, str) else str(raw)

        # 去掉 <think> ... </think> 这种思维噪声，避免干扰 JSON 提取
        raw_text_no_think = re.sub(
            r"<think>.*?</think>", "", raw_text, flags=re.S | re.I
        ).strip()

        data: Dict[str, Any] | None = None

        # 1) 优先从 ```json ... ``` 代码块中提取
        try:
            code_block_match = re.search(
                r"```json\s*(\{.*?\})\s*```", raw_text_no_think, flags=re.S | re.I
            )
            if code_block_match:
                json_str = code_block_match.group(1)
                data = json.loads(json_str)
        except Exception as e:
            logger.warning("Failed to parse JSON from ```json``` block: %s", e)

        # 2) 如果没有 ```json``` 块或解析失败，再尝试匹配第一个 { ... }
        if data is None:
            try:
                match = re.search(r"\{.*\}", raw_text_no_think, re.S)
                if match:
                    data = json.loads(match.group(0))
            except Exception as e:
                logger.warning("Failed to parse JSON from first {...} block: %s", e)

        # 3) 如果还是不行，使用兜底方案
        if data is None or not isinstance(data, dict):
            logger.warning("Failed to parse planning JSON, fallback to default planning")
            data = {
                "sub_questions": [question],
                "keywords": [question],
                "max_papers": 10,
            }

        sub_questions = data.get("sub_questions") or [question]
        keywords = data.get("keywords") or [question]
        max_papers_raw = data.get("max_papers") or 10
        try:
            max_papers = int(max_papers_raw)
        except Exception:
            max_papers = 10

        print(
            {
                "sub_questions": sub_questions,
                "keywords": keywords,
                "max_papers": max_papers,
            }
        )

        return {
            "sub_questions": sub_questions,
            "keywords": keywords,
            "max_papers": max_papers,
        }
    

    def _synthesize_hypotheses(
        self,
        question: str,
        planning: Dict[str, Any],
        papers: List[Dict[str, Any]],
        graph_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        使用 LLM 在文献与图谱增量的基础上生成：
        - 候选假设列表（每条包含动机、关键证据、潜在反驳）
        - 粗略研究方案（数据/方法/评价指标的草图）
        """
        # 为了减小 prompt 体积，只抽取前若干篇文献摘要
        top_papers = papers[: min(len(papers), 8)]

        paper_snippets = []
        for p in top_papers:
            title = p.get("title", "")
            abstract = p.get("summary") or p.get("abstract") or ""
            paper_snippets.append(f"- {title}\n  {abstract}")

        context = "\n\n".join(paper_snippets)

        system_prompt = (
            "你是一个跨学科 AI 科学家助手。"
            "给定科研问题、子问题、若干关键文献摘要以及知识图谱的增量统计，"
            "请生成一组候选科研假设以及配套的初步研究方案。"
            "输出必须是 JSON，包含字段：\n"
            "hypotheses: 列表，每项含 id, title, rationale, evidence, possible_risks\n"
            "plan: 列表，每项含 step, description, related_hypotheses\n"
        )

        user_prompt = (
            f"科研问题：\n{question}\n\n"
            f"子问题列表：\n{planning['sub_questions']}\n\n"
            f"知识图谱增量统计：\n{graph_stats}\n\n"
            f"相关文献（截断版）：\n{context}\n\n"
            "请直接输出 JSON，用```json```包裹，不要带多余文字。"
        )

        raw = self.llm.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        text = raw.strip()
        if "</think>" in text:
            text = text.split("</think>", 1)[1].strip()

        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        elif text.startswith("```"):
            text = text[3:]  # Remove ```

        if text.endswith("```"):
            text = text[:-3]  # Remove closing ```

        text = text.strip()

        import json

        try:
            data = json.loads(text)
        except Exception:
            logger.warning("Failed to parse hypotheses JSON, fallback to simple structure")
            data = {
                "hypotheses": [
                    {
                        "id": "H1",
                        "title": "Initial hypothesis from EvoVerse-MVP",
                        "rationale": raw[:500],
                        "evidence": [],
                        "possible_risks": [],
                    }
                ],
                "plan": [],
            }

        return {
            "hypotheses": data.get("hypotheses", []),
            "plan": data.get("plan", []),
        }

    # ------------------------------------------------------------------
    # TaskRecord 辅助
    # ------------------------------------------------------------------

    def _create_task_record(self, task_id: str, question: str) -> TaskRecord:
        """在关系数据库中创建一条任务记录。"""
        with get_session() as session:
            record = TaskRecord(
                id=task_id,
                agent_id=self.agent_id,
                task_type="research_mvp",
                input_data={"question": question},
                status="running",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
            )
            session.add(record)
            session.commit()
            return record

    def _complete_task_record(self, record: TaskRecord, result: Dict[str, Any]) -> None:
        """任务成功完成时更新任务记录。"""
        with get_session() as session:
            db_record = session.query(TaskRecord).filter_by(id=record.id).first()
            if not db_record:
                return
            db_record.status = "completed"  # type: ignore
            db_record.output_data = result  # type: ignore
            db_record.completed_at = datetime.utcnow() # type: ignore
            session.commit()

    def _fail_task_record(self, record: TaskRecord, error_message: str) -> None:
        """任务失败时更新任务记录。"""
        with get_session() as session:
            db_record = session.query(TaskRecord).filter_by(id=record.id).first()
            if not db_record:
                return
            db_record.status = "failed"  # type: ignore
            db_record.error_message = error_message  # type: ignore
            db_record.completed_at = datetime.utcnow()  # type: ignore
            session.commit()

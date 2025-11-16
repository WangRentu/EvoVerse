"""
KnowledgeAgent - MVP 知识图谱 Agent

封装 GraphBuilder / KnowledgeGraph，负责将文献写入知识图谱和向量库。
"""

from typing import Any, Dict, List, Optional
import logging

from evoverse.agents.base_agent import BaseAgent
from evoverse.knowledge.graph_builder import GraphBuilder
from evoverse.literature.base_client import PaperMetadata, PaperSource


logger = logging.getLogger(__name__)


class KnowledgeAgent(BaseAgent):
    """MVP 版本知识图谱 Agent。"""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        graph_builder: Optional[GraphBuilder] = None,
    ):
        super().__init__(agent_id=agent_id, agent_type="KnowledgeAgent", config=config)
        self.builder = graph_builder or GraphBuilder()

    def ingest_papers(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        将文献列表写入知识图谱。

        这里的 papers 来自 LiteratureAgent.simplify 后的 dict，需要转回
        PaperMetadata 以便 GraphBuilder 使用。

        预期字段：
        {
            "id": str,           # 统一逻辑 ID: arxiv:xxxx / pubmed:xxxx / ...
            "source": str,       # "arxiv" / "pubmed" / "unknown" ...
            "primary_id": Any,   # 原始源内部 ID，可选
            "title": str,
            "authors": [str],
            "year": int | None,
            "abstract": str,
            "summary": str,
        }
        """
        if not papers:
            return {"papers_ingested": 0, "errors": 0}

        minimal_papers: List[PaperMetadata] = []
        errors = 0

        for p in papers:
            try:
                # 1. 必须有 id，没有就跳过
                paper_id = p.get("id")
                if not paper_id:
                    errors += 1
                    logger.warning("Skip paper without id: %r", p)
                    continue

                # 2. source 现在已经是字符串（arxiv/pubmed/unknown）
                source_str = (p.get("source") or "unknown")
                source_enum = PaperSource(source_str) if source_str in PaperSource._value2member_map_ else PaperSource.UNKNOWN

                # 3. 构造最小 PaperMetadata（和 Kosmos 一样：id + source + 基本元数据）
                meta = PaperMetadata(
                    id=paper_id,
                    title=p.get("title", "") or "",
                    abstract=p.get("abstract") or p.get("summary") or "",
                    authors=p.get("authors") or [],
                    year=p.get("year", None),
                    source=source_enum,
                    # 如果 PaperMetadata 里还有 primary_id 之类字段，可以顺手加上：
                    # primary_id=p.get("primary_id"),
                )
                minimal_papers.append(meta)

            except Exception as exc:  # noqa: BLE001
                errors += 1
                logger.warning(
                    "Failed to build PaperMetadata from simplified paper: %s; data=%r",
                    exc,
                    p,
                )

        if not minimal_papers:
            stats = {"papers_ingested": 0, "errors": errors}
            logger.info("KnowledgeAgent ingestion stats: %s", stats)
            return stats

        logger.info(
            "KnowledgeAgent ingesting %d papers into knowledge graph",
            len(minimal_papers),
        )

        # 写入知识图谱和向量库（先关掉复杂关系，MVP 只塞 paper 节点）
        self.builder.build_from_papers(
            minimal_papers,
            extract_concepts=False,
            add_authors=False,
            add_citations=False,
            add_semantic_relationships=False,
            show_progress=False,
        )

        stats = {
            "papers_ingested": self.builder.stats.get("papers_added", 0),
            "errors": errors + self.builder.stats.get("errors", 0),
        }

        logger.info("KnowledgeAgent ingestion stats: %s", stats)
        return stats


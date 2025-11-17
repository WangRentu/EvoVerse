"""
KnowledgeAgent - MVP 知识图谱 Agent

封装 GraphBuilder / KnowledgeGraph，负责将文献写入知识图谱和向量库。
"""

from typing import Any, Dict, List, Optional
import logging

from evoverse.agents.base_agent import BaseAgent
from evoverse.knowledge.graph_builder import GraphBuilder
from evoverse.literature.base_client import PaperMetadata, PaperSource, Author


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
                source_enum = (
                    PaperSource(source_str)
                    if source_str in PaperSource._value2member_map_
                    else PaperSource.UNKNOWN
                )

                primary_id = p.get("primary_id")

                # 3. 规范作者列表为 Author 对象列表（GraphBuilder 需要 .name/.affiliation）
                raw_authors = p.get("authors") or []
                authors: List[Author] = []
                for a in raw_authors:
                    if isinstance(a, str):
                        name = a.strip()
                    elif isinstance(a, dict):
                        name = (a.get("name") or "").strip()
                    else:
                        name = str(a).strip()

                    if not name:
                        continue

                    affiliation = None
                    if isinstance(a, dict):
                        affiliation = a.get("affiliation")

                    authors.append(Author(name=name, affiliation=affiliation))

                # 4. 映射主 ID 到具体字段，尽量贴合底层 schema
                doi = None
                arxiv_id = None
                pubmed_id = None

                if primary_id:
                    pid_str = str(primary_id).strip()
                    if source_enum == PaperSource.ARXIV:
                        arxiv_id = pid_str
                    elif source_enum == PaperSource.PUBMED:
                        pubmed_id = pid_str
                    else:
                        # 其他来源先只保留在 id 里，后续需要可以扩展
                        pass

                # 5. 构造 PaperMetadata（包含标题、摘要、作者、年份等）
                meta = PaperMetadata(
                    id=paper_id,
                    source=source_enum,
                    doi=doi,
                    arxiv_id=arxiv_id,
                    pubmed_id=pubmed_id,
                    title=p.get("title", "") or "",
                    abstract=p.get("abstract") or p.get("summary") or "",
                    authors=authors,
                    year=p.get("year", None),
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

        # 从配置中读取开关，默认打开完整建图流程
        cfg = self.config or {}
        extract_concepts = cfg.get("extract_concepts", True)
        add_authors = cfg.get("add_authors", True)
        add_citations = cfg.get("add_citations", True)
        add_semantic_relationships = cfg.get(
            "add_semantic_relationships",
            True,
        )

        # 写入知识图谱和向量库（默认启用概念/方法/作者/引文/语义关系）
        self.builder.build_from_papers(
            minimal_papers,
            extract_concepts=extract_concepts,
            add_authors=add_authors,
            add_citations=add_citations,
            add_semantic_relationships=add_semantic_relationships,
            show_progress=False,
        )

        stats = {
            "papers_ingested": self.builder.stats.get("papers_added", 0),
            "errors": errors + self.builder.stats.get("errors", 0),
        }

        logger.info("KnowledgeAgent ingestion stats: %s", stats)
        return stats

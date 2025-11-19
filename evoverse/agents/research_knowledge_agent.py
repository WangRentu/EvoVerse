"""
KnowledgeAgent - MVP 知识图谱 Agent

封装 GraphBuilder / KnowledgeGraph，负责将文献写入知识图谱和向量库。
"""

from typing import Any, Dict, List, Optional, Set
import logging

from evoverse.agents.base_agent import BaseAgent
from evoverse.knowledge.graph_builder import GraphBuilder
from evoverse.literature.base_client import PaperMetadata, PaperSource, Author
from evoverse.literature.unified_search import UnifiedLiteratureSearch


logger = logging.getLogger(__name__)


class KnowledgeAgent(BaseAgent):
    """MVP 版本知识图谱 Agent。"""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        graph_builder: Optional[GraphBuilder] = None,
        literature_search: Optional[UnifiedLiteratureSearch] = None,
    ):
        super().__init__(agent_id=agent_id, agent_type="KnowledgeAgent", config=config)
        self.builder = graph_builder or GraphBuilder()
        # 引用边依赖的参考文献检索器，默认启用 Semantic Scholar / PubMed 等
        try:
            self.reference_searcher = literature_search or UnifiedLiteratureSearch()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to initialize literature searcher for references: %s", exc)
            self.reference_searcher = None
        self._reference_cache: Dict[str, List[PaperMetadata]] = {}
        self._citation_cache: Dict[str, List[PaperMetadata]] = {}

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

        cfg = self.config or {}
        extract_concepts = cfg.get("extract_concepts", True)
        add_authors = cfg.get("add_authors", True)
        add_citations = cfg.get("add_citations", True)
        add_semantic_relationships = cfg.get("add_semantic_relationships", True)
        fetch_references = cfg.get("fetch_references", True)
        fetch_citations = cfg.get("fetch_citations", True)
        max_references = cfg.get("max_references_per_paper", 25)
        max_citations = cfg.get("max_citations_per_paper", 25)

        minimal_papers: List[PaperMetadata] = []
        supplemental_pool: Dict[str, PaperMetadata] = {}
        ingested_ids: Set[str] = set()
        errors = 0

        for p in papers:
            try:
                paper_id = p.get("id")
                if not paper_id:
                    errors += 1
                    logger.warning("Skip paper without id: %r", p)
                    continue

                source_str = (p.get("source") or "unknown")
                source_enum = (
                    PaperSource(source_str)
                    if source_str in PaperSource._value2member_map_
                    else PaperSource.UNKNOWN
                )

                primary_id = p.get("primary_id")

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

                    affiliation = a.get("affiliation") if isinstance(a, dict) else None
                    authors.append(Author(name=name, affiliation=affiliation))

                doi = None
                arxiv_id = None
                pubmed_id = None

                if primary_id:
                    pid_str = str(primary_id).strip()
                    if source_enum == PaperSource.ARXIV:
                        arxiv_id = pid_str
                    elif source_enum == PaperSource.PUBMED:
                        pubmed_id = pid_str

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

                self._populate_references_for_metadata(
                    meta,
                    existing_reference_ids=p.get("references"),
                    add_citations=add_citations,
                    fetch_references=fetch_references,
                    max_refs=max_references,
                    reference_pool=supplemental_pool,
                    fetch_citations=fetch_citations,
                    max_citations=max_citations,
                    reference_owner_id=meta.primary_identifier,
                )

                minimal_papers.append(meta)
                ingested_ids.add(meta.primary_identifier)

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

        self.builder.build_from_papers(
            minimal_papers,
            extract_concepts=extract_concepts,
            add_authors=add_authors,
            add_citations=add_citations,
            add_semantic_relationships=add_semantic_relationships,
            show_progress=False,
        )

        reference_added = 0
        if add_citations:
            reference_added = self._ingest_reference_only_papers(supplemental_pool, ingested_ids)

        stats = {
            "papers_ingested": self.builder.stats.get("papers_added", 0),
            "reference_papers_ingested": reference_added,
            "errors": errors + self.builder.stats.get("errors", 0),
        }

        logger.info("KnowledgeAgent ingestion stats: %s", stats)
        return stats

    def analyze_and_ingest(self, papers: List[Dict[str, Any]], enable_deep_analysis: bool = True) -> Dict[str, Any]:
        """
        智能分析并写入知识图谱。

        这个方法结合了文献分析和图谱构建，提供完整的知识摄入流程：
        1. 对论文进行深度分析（如果启用）
        2. 提取概念、方法、关系
        3. 构建完整的知识图谱（包括语义相似性边）
        4. 返回详细的统计信息

        Args:
            papers: 论文数据列表（来自 LiteratureAgent）
            enable_deep_analysis: 是否启用深度分析

        Returns:
            完整的摄入统计信息
        """
        if not papers:
            return {"papers_ingested": 0, "errors": 0, "analyses_performed": 0}

        # 从配置读取通用开关
        cfg = self.config or {}
        extract_concepts = cfg.get("extract_concepts", True)
        add_authors = cfg.get("add_authors", True)
        add_citations = cfg.get("add_citations", True)
        add_semantic_relationships = cfg.get("add_semantic_relationships", True)
        fetch_references = cfg.get("fetch_references", True)
        fetch_citations = cfg.get("fetch_citations", True)
        max_references = cfg.get("max_references_per_paper", 25)
        max_citations = cfg.get("max_citations_per_paper", 25)

        # 如果启用深度分析，先进行分析
        analyses = []
        if enable_deep_analysis:
            from .research_literature_agent import LiteratureAgent
            literature_agent = LiteratureAgent()

            logger.info(f"开始深度分析 {len(papers)} 篇论文...")

            for i, paper in enumerate(papers):
                if i % 5 == 0:  # 每5篇打印一次进度
                    logger.info(f"分析进度: {i+1}/{len(papers)}")

                try:
                    analysis = literature_agent.analyze_paper_deep(paper)
                    analyses.append(analysis)

                    # 将分析结果添加到论文数据中
                    paper["deep_analysis"] = analysis.to_dict()

                except Exception as e:
                    logger.error(f"深度分析失败 {paper.get('id', 'unknown')}: {e}")
                    analyses.append(None)

            logger.info(f"完成 {len([a for a in analyses if a is not None])} 篇论文的深度分析")
        else:
            logger.info("跳过深度分析，使用现有摘要")

        # 现在进行标准的图谱摄入
        logger.info("开始知识图谱摄入...")

        # 转换论文格式
        minimal_papers = []
        errors = 0
        supplemental_pool: Dict[str, PaperMetadata] = {}
        ingested_ids: Set[str] = set()

        for p in papers:
            try:
                paper_id = p.get("id")
                if not paper_id:
                    errors += 1
                    continue

                source_str = (p.get("source") or "unknown")
                source_enum = (
                    PaperSource(source_str)
                    if source_str in PaperSource._value2member_map_
                    else PaperSource.UNKNOWN
                )

                primary_id = p.get("primary_id")

                # 规范作者列表
                raw_authors = p.get("authors") or []
                authors = []
                for a in raw_authors:
                    if isinstance(a, str):
                        name = a.strip()
                        affiliation = None
                    elif isinstance(a, dict):
                        name = (a.get("name") or "").strip()
                        affiliation = a.get("affiliation")
                    else:
                        name = str(a).strip()
                        affiliation = None

                    if name:
                        authors.append(Author(name=name, affiliation=affiliation))

                # 映射主ID到具体字段
                doi = None
                arxiv_id = None
                pubmed_id = None

                if primary_id:
                    pid_str = str(primary_id).strip()
                    if source_enum == PaperSource.ARXIV:
                        arxiv_id = pid_str
                    elif source_enum == PaperSource.PUBMED:
                        pubmed_id = pid_str

                # 构造PaperMetadata
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

                # 如果有深度分析结果，添加到 full_text 中
                deep_analysis = p.get("deep_analysis")
                if isinstance(deep_analysis, dict):
                    exec_summary = deep_analysis.get("executive_summary", "") or ""

                    # 关键发现：兼容字符串列表或 {finding: "..."} 列表
                    key_findings_items = deep_analysis.get("key_findings", []) or []
                    key_finding_lines: List[str] = []
                    for item in key_findings_items:
                        if isinstance(item, dict):
                            text = item.get("finding") or item.get("text") or ""
                        else:
                            text = str(item)
                        text = text.strip()
                        if text:
                            key_finding_lines.append(f"- {text}")
                    key_findings_block = chr(10).join(key_finding_lines)

                    methodology = deep_analysis.get("methodology", {})
                    significance = deep_analysis.get("significance", "") or ""

                    # 局限性：通常是字符串列表
                    limitations_items = deep_analysis.get("limitations", []) or []
                    limitation_lines = [str(l).strip() for l in limitations_items if str(l).strip()]
                    limitations_block = chr(10).join(limitation_lines)

                    analysis_text = f"""
执行摘要：{exec_summary}

关键发现：
{key_findings_block}

方法论：{methodology}

重要性：{significance}

局限性：
{limitations_block}
                    """.strip()
                    meta.full_text = analysis_text

                self._populate_references_for_metadata(
                    meta,
                    existing_reference_ids=p.get("references"),
                    add_citations=add_citations,
                    fetch_references=fetch_references,
                    max_refs=max_references,
                    reference_pool=supplemental_pool,
                    fetch_citations=fetch_citations,
                    max_citations=max_citations,
                    reference_owner_id=meta.primary_identifier,
                )

                minimal_papers.append(meta)
                ingested_ids.add(meta.primary_identifier)

            except Exception as exc:
                errors += 1
                logger.warning(f"构建 PaperMetadata 失败: {exc}; 数据={p}")

        if not minimal_papers:
            return {"papers_ingested": 0, "errors": errors, "analyses_performed": len([a for a in analyses if a is not None])}

        # 摄入知识图谱
        logger.info(f"将 {len(minimal_papers)} 篇论文写入知识图谱...")

        # 执行图谱构建
        self.builder.build_from_papers(
            minimal_papers,
            extract_concepts=extract_concepts,
            add_authors=add_authors,
            add_citations=add_citations,
            add_semantic_relationships=add_semantic_relationships,
            show_progress=False,
        )

        reference_added = 0
        if add_citations:
            reference_added = self._ingest_reference_only_papers(supplemental_pool, ingested_ids)

        # 构建详细统计
        stats = {
            "papers_ingested": self.builder.stats.get("papers_added", 0),
            "authors_added": self.builder.stats.get("authors_added", 0),
            "concepts_extracted": self.builder.stats.get("concepts_added", 0),
            "methods_extracted": self.builder.stats.get("methods_added", 0),
            "citations_added": self.builder.stats.get("citations_added", 0),
            "relationships_created": self.builder.stats.get("relationships_added", 0),
            "semantic_edges": 0,  # 稍后可以从图统计中获取
            "analyses_performed": len([a for a in analyses if a is not None]),
            "reference_papers_ingested": reference_added,
            "errors": errors + self.builder.stats.get("errors", 0)
        }

        # 获取图数据库统计
        try:
            graph_stats = self.builder.get_build_stats().get("graph_stats", {})
            stats["semantic_edges"] = graph_stats.get("semantically_similar_count", 0)
        except Exception:
            pass

        logger.info(f"智能摄入完成: {stats}")
        return stats

    def _populate_references_for_metadata(
        self,
        metadata: PaperMetadata,
        *,
        existing_reference_ids: Optional[List[str]],
        add_citations: bool,
        fetch_references: bool,
        max_refs: int,
        reference_pool: Dict[str, PaperMetadata],
        fetch_citations: bool,
        max_citations: int,
        reference_owner_id: Optional[str],
    ) -> None:
        """
        Ensure PaperMetadata carries a list of referenced paper IDs and
        collect referenced/citing PaperMetadata objects for later ingestion.
        """
        references: List[str] = []

        if existing_reference_ids:
            for ref in existing_reference_ids:
                ref_id = (str(ref).strip()) if ref else ""
                if ref_id:
                    references.append(ref_id)
        elif (
            add_citations
            and fetch_references
            and metadata.source == PaperSource.SEMANTIC_SCHOLAR
        ):
            fetched = self._fetch_references_for_paper(metadata, max_refs)
            for ref in fetched:
                ref_id = ref.primary_identifier
                if not ref_id:
                    continue
                if ref_id not in references:
                    references.append(ref_id)
                if ref_id not in reference_pool:
                    reference_pool[ref_id] = ref

        if references:
            metadata.references = references

        if (
            add_citations
            and fetch_citations
            and metadata.source == PaperSource.SEMANTIC_SCHOLAR
            and reference_owner_id
        ):
            citing_papers = self._fetch_citations_for_paper(metadata, max_citations)
            for citing in citing_papers:
                citing_id = citing.primary_identifier
                if not citing_id:
                    continue

                current_refs = citing.references or []
                if reference_owner_id not in (current_refs or []):
                    updated = list(current_refs or [])
                    updated.append(reference_owner_id)
                    citing.references = updated

                if citing_id not in reference_pool:
                    reference_pool[citing_id] = citing

    def _fetch_references_for_paper(
        self,
        paper: PaperMetadata,
        max_refs: int
    ) -> List[PaperMetadata]:
        """Fetch references for a paper using the unified literature searcher."""
        if not self.reference_searcher:
            return []

        if paper.source != PaperSource.SEMANTIC_SCHOLAR:
            return []

        pid = (paper.raw_data or {}).get("paperId")
        if not pid:
            return []

        if pid in self._reference_cache:
            return self._reference_cache[pid]

        try:
            refs = self.reference_searcher.get_references(paper, max_references=max_refs)
            self._reference_cache[pid] = refs or []
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch references for %s: %s", pid, exc)
            self._reference_cache[pid] = []

        return self._reference_cache[pid]

    def _fetch_citations_for_paper(
        self,
        paper: PaperMetadata,
        max_citations: int
    ) -> List[PaperMetadata]:
        """Fetch citing papers for a given paper."""
        if not self.reference_searcher:
            return []

        if paper.source != PaperSource.SEMANTIC_SCHOLAR:
            return []

        pid = (paper.raw_data or {}).get("paperId")
        if not pid:
            return []

        if pid in self._citation_cache:
            return self._citation_cache[pid]

        try:
            cites = self.reference_searcher.get_citations(
                paper,
                max_citations=max_citations
            )
            self._citation_cache[pid] = cites or []
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch citations for %s: %s", pid, exc)
            self._citation_cache[pid] = []

        return self._citation_cache[pid]

    def _ingest_reference_only_papers(
        self,
        reference_pool: Dict[str, PaperMetadata],
        ingested_ids: Set[str]
    ) -> int:
        """
        Add referenced papers (without heavy extraction) so citation edges have endpoints.
        """
        added = 0
        for ref_id, reference_meta in reference_pool.items():
            if ref_id in ingested_ids:
                continue

            try:
                self.builder.add_paper(
                    reference_meta,
                    extract_concepts=False,
                    add_authors=bool(reference_meta.authors),
                    add_citations=False
                )
                ingested_ids.add(ref_id)
                added += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to ingest reference paper %s: %s", ref_id, exc)

        if added:
            logger.info("Added %d referenced papers for citation edges", added)

        return added

"""
LiteratureAgent - MVP 文献检索 Agent

封装 UnifiedLiteratureSearch，提供：
- search_and_summarize：按查询检索文献并用 LLM 做简要摘要
"""

from typing import Any, Dict, List, Optional
import logging

from evoverse.agents.base_agent import BaseAgent
from evoverse.literature.unified_search import UnifiedLiteratureSearch
from evoverse.core.llm_client import LLMClient
import hashlib


logger = logging.getLogger(__name__)


class LiteratureAgent(BaseAgent):
    """MVP 版本文献 Agent。"""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        llm_client: Optional[LLMClient] = None,
        searcher: Optional[UnifiedLiteratureSearch] = None,
    ):
        super().__init__(agent_id=agent_id, agent_type="LiteratureAgent", config=config)
        self.llm = llm_client or LLMClient(max_history=16)
        # 默认关闭 Semantic Scholar，以减少网络依赖和不稳定性
        self.searcher = searcher or UnifiedLiteratureSearch(
            semantic_scholar_enabled=False
        )

    @staticmethod
    def _build_global_id(
        source: Optional[str],
        primary_id: Optional[str],
        title: str,
        year: Optional[int],
    ) -> str:
        """
        为每篇论文构造一个全局唯一的逻辑 ID，类似 Kosmos：
        arxiv:2511.02824
        pubmed:12345678
        semanticscholar:abcdef1234
        如果缺少 primary_id，就用 title+year 做一个短 hash。
        """
        src = (source or "unknown").lower()

        # 优先用 source + primary_id
        if primary_id:
            pid = str(primary_id).strip()
            return f"{src}:{pid}"

        # 兜底：用标题 + 年份构造一个稳定 hash
        base = f"{title}|{year or ''}".encode("utf-8")
        digest = hashlib.sha1(base).hexdigest()[:16]
        return f"{src}:{digest}"

    def search_and_summarize(
        self,
        query: str,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        检索文献并为每篇生成简短摘要。

        返回的每个元素是经过精简的 dict，方便后续序列化和 prompt 使用：
        {
            "title": ...,
            "authors": [...],
            "year": ...,
            "abstract": ...,
            "summary": ...,
            "source": ...,
            "primary_id": ...
        }
        """
        logger.info("LiteratureAgent searching papers: %s", query)
        papers = self.searcher.search(
            query=query,
            max_results_per_source=max_results,
            total_max_results=max_results,
            deduplicate=True,
            extract_full_text=False,
        )
        for i, p in enumerate(papers, start=1):
            logger.info(
                "Paper %d: [%s] %s",
                i,
                getattr(p, "primary_identifier", getattr(p, "id", "")),
                getattr(p, "title", ""),
            )

        simplified: List[Dict[str, Any]] = []
        for p in papers:
            simplified.append(self._simplify_paper(p))

        # 用 LLM 生成摘要（批量处理可以后续优化，MVP 先简单逐篇）
        for item in simplified:
            item["summary"] = self._summarize_paper(item)

        logger.info("LiteratureAgent retrieved %d papers", len(simplified))
        return simplified

    def _simplify_paper(self, paper: Any) -> Dict[str, Any]:
        """将 PaperMetadata 压缩成易于传输和序列化的字典，并补充统一 ID。"""
        # 1. 取基础字段
        title = getattr(paper, "title", "") or ""
        authors = getattr(paper, "authors", []) or []
        year = getattr(paper, "year", None)
        abstract = getattr(paper, "abstract", None) or getattr(paper, "summary", "")
        source = getattr(paper, "source", None)
        primary_id = getattr(paper, "primary_identifier", None)

        # 2. 规范作者列表为 List[str]
        norm_authors: List[str] = []
        for a in authors:
            if isinstance(a, str):
                norm_authors.append(a)
            else:
                name = getattr(a, "name", None) or str(a)
                norm_authors.append(name)

        # 3. 规范 source 为字符串
        if source is None:
            source_str = "unknown"
        else:
            source_str = getattr(source, "value", str(source)).lower()

        # 4. 构造统一逻辑 ID（和 Kosmos 一样的思路）
        global_id = self._build_global_id(
            source=source_str,
            primary_id=primary_id,
            title=title,
            year=year,
        )

        # 5. 返回带 id 的简化结构
        return {
            "id": global_id,          # 🔴 统一的内部 ID（后面所有地方都用它）
            "source": source_str,     # 文献来源：arxiv / pubmed / semanticscholar / unknown
            "primary_id": primary_id, # 原始 source 的主键，方便 debug 或外部跳转
            "title": title,
            "authors": norm_authors,
            "year": year,
            "abstract": abstract,
            "summary": "",            # 这里先留空，后面 _summarize_paper 再填
        }
    

    def _summarize_paper(self, paper: Dict[str, Any]) -> str:
        """使用 LLM 为单篇文献生成 2-3 句中文摘要。"""
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")

        if not abstract:
            return ""

        messages = [
            {
                "role": "system",
                "content": "你是科研助手，请用中文用 2-3 句总结论文要点。",
            },
            {
                "role": "user",
                "content": f"论文标题：{title}\n\n摘要：{abstract}",
            },
        ]

        try:
            summary = self.llm.chat(messages)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM summarize paper failed: %s", exc)
            summary = ""

        return summary

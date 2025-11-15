# EvoVerse

**EvoVerse** 是一个面向未来的 **多智能体科研系统（Multi-Agent Scientific Ecosystem）**，旨在让 AI 不只是回答问题，而是真正像“科研群体”一样进行协作、推理、演化与创新。  
它将跨学科知识组织、智能体协作机制与演化式优化结合在一起，构建一个可持续增长的 AI 科学生态系统。

---

## 🌌 核心理念

EvoVerse 的核心思想可以概括为三点：

### 1. **多智能体协作（Agent Society）**
EvoVerse 将科研任务拆分给多个具备不同能力的智能体：  
推理、文献检索、假设生成、实验设计、结果分析、知识整合……  
它们像一个“科研小组”，相互协同、互相对抗、互相启发。

### 2. **跨学科知识超图（Hypergraph Knowledge Space）**
世界知识不是树状的，而是跨域交织的。  
EvoVerse 使用 **本体 + 超图** 的结构，来表达跨学科关系，让模型能够：

- 跨学科联想  
- 跳跃式推理  
- 从复杂网络中挖掘新的科学连接  

这是系统能够进行“跨学科创新”的核心基础。

### 3. **演化式科研循环（Evolutionary Scientific Discovery）**
EvoVerse 不追求一次性答案。  
它设计成 **“持续演化的科学循环”**：

1. 生成假设  
2. 反驳与评审  
3. 整合证据  
4. 迭代生成更优秀的理论  
5. 将知识写回全局超图  

这个过程不断展开，形成一个会自我成长的科研宇宙（Universe），因此命名为 **EvoVerse**。

---

## 🧠 项目定位

EvoVerse 面向以下目标：

- 构建一个 **可持续增长的 AI 科研智能体生态系统**
- 打造一个能够 **跨学科提出新想法、设计实验、并验证推理链条** 的平台
- 让 LLM 成为 **科学知识的构建者，而不是信息的复述者**
- 使科研过程具备：竞争、合作、协同、演化、记忆、知识积累等能力

它不是单一模型，而是一个 **智能体宇宙**。

---

## 🚀 EvoVerse 的愿景

EvoVerse 旨在成为：

- 一个 **类脑式 AI 科学思考框架**
- 一个 **跨学科知识融合引擎**
- 一个 **多智能体竞争-合作的科研生态**
- 一个可以 **不断演化、不断积累知识的 AI 科研世界**

最终目标是：  
**让 AI 和科学家的智能群体一起推动科学发现的速度与边界。**

---

## 📚 灵感来源

EvoVerse 的设计受到以下方向的启发：

- Agentic Organization（多智能体组织架构）
- AI Co-Scientist（AI 科学家框架）
- HyperGraphRAG（超图式知识检索）
- Ontology-Driven Reasoning（本体驱动推理）
- Evolutionary Game Theory（演化博弈）
- Cognitive Architectures（认知架构）

但 EvoVerse 并不是这些工作的复刻，而是将它们整合成一个 **面向跨学科科研的统一框架**。

---

## 🌱 当前状态

EvoVerse 还处于早期阶段，专注于：

- 构建项目基础框架
- 实现多智能体基础协议
- 设计知识表示与演化循环

未来版本将加入：

- 文献检索系统  
- 跨学科超图知识库  
- 可视化智能体协作界面  
- 演化策略优化  
- 实验设计与分析引擎  

---
## 📄 文献系统（已迁移自 Kosmos）

- arXiv / Semantic Scholar / PubMed 三源并行检索，统一 `PaperMetadata` 结构
- PDF 下载与 PyMuPDF 文本抽取，支持磁盘缓存与全文拼接
- BibTeX / RIS 解析与导出、引用网络分析、参考文献管理
- 统一搜索器 `UnifiedLiteratureSearch` 自动去重、排序、可选全文抽取

### 运行依赖

```bash
pip install arxiv semanticscholar biopython pymupdf httpx bibtexparser networkx tenacity
```

（还需要 `requests`, `beautifulsoup4` 等常规依赖，如果环境缺失请一并安装。）

### 配置项（.env）

| 变量 | 作用 |
| --- | --- |
| `LITERATURE_SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API Key，提升配额 |
| `LITERATURE_PUBMED_API_KEY` | PubMed API Key（可选） |
| `LITERATURE_PUBMED_EMAIL` | PubMed 要求的联系邮箱 |
| `LITERATURE_CACHE_DIR` | 文献 API 缓存目录（默认 `.literature_cache`） |
| `LITERATURE_CACHE_TTL_HOURS` | 缓存过期时间（默认 48 小时） |
| `LITERATURE_MAX_CACHE_SIZE_MB` | 缓存最大体积（默认 1GB） |
| `LITERATURE_MAX_RESULTS_PER_QUERY` | 每源最大返回条数（默认 100） |
| `LITERATURE_PDF_DOWNLOAD_TIMEOUT` | PDF 下载超时，秒（默认 30） |

配置加载后即可直接通过 `from evoverse.literature import UnifiedLiteratureSearch` 使用完整功能。

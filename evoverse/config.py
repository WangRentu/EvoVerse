# evoverse/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class LLMConfig(BaseSettings):
    base_url: str = Field(default="http://localhost:11434/v1")
    api_key: str = Field(default="ollama")
    model: str = Field(default="qwen3:30b-a3b-thinking-2507-fp16")
    temperature: float = 0.2
    max_tokens: int = 2048
    request_timeout: float = Field(
        default=30.0,
        description="LLM 请求超时时间（秒），避免长时间无响应"
    )

    model_config = {
        "env_prefix": "LLM_",
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }


class DatabaseConfig(BaseSettings):
    url: str = "sqlite:///evoverse.db"
    echo: bool = False

    model_config = {
        "env_prefix": "DB_",
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }

class MemoryConfig(BaseSettings):
    """记忆系统配置"""
    max_memories: int = Field(default=1000, description="最大记忆条数")
    prune_after_days: int = Field(default=30, description="记忆过期天数")
    min_importance_to_keep: float = Field(default=0.3, description="保留最小重要性")
    enable_persistence: bool = Field(default=True, description="启用记忆持久化")

    model_config = {
        "env_prefix": "MEMORY_",
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }


class Neo4jConfig(BaseSettings):
    """Neo4j 知识图谱配置"""
    uri: str = Field(default="bolt://localhost:7687", description="Neo4j 连接 URI")
    user: str = Field(default="neo4j", description="Neo4j 用户名")
    password: str = Field(default="password", description="Neo4j 密码")
    database: str = Field(default="neo4j", description="Neo4j 数据库名")
    max_connection_lifetime: int = Field(default=3600, description="最大连接生命周期（秒）")
    max_connection_pool_size: int = Field(default=50, description="最大连接池大小")

    model_config = {
        "env_prefix": "NEO4J_",
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }



class LiteratureConfig(BaseSettings):
    """文献检索配置"""
    semantic_scholar_api_key: Optional[str] = Field(default=None, description="Semantic Scholar API Key")
    pubmed_api_key: Optional[str] = Field(default=None, description="PubMed API Key")
    pubmed_email: Optional[str] = Field(default=None, description="PubMed 联系邮箱")
    cache_dir: str = Field(default=".literature_cache", description="缓存目录")
    cache_ttl_hours: int = Field(default=48, description="缓存 TTL (小时)")
    max_cache_size_mb: int = Field(default=1000, description="缓存最大大小 (MB)")
    max_results_per_query: int = Field(default=100, description="单次检索最大结果数")
    pdf_download_timeout: int = Field(default=30, description="PDF 下载超时 (秒)")

    model_config = {
        "env_prefix": "LITERATURE_",
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }


class KnowledgeConfig(BaseSettings):
    """知识图谱系统配置"""
    enable_neo4j: bool = Field(default=True, description="启用 Neo4j 知识图谱")
    enable_vector_db: bool = Field(default=True, description="启用向量数据库")
    vector_db_path: str = Field(default="./vector_db", description="向量数据库路径")
    chroma_persist_directory: str = Field(default=".chroma_db", description="ChromaDB 持久化目录")

    model_config = {
        "env_prefix": "KNOWLEDGE_",
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }


class EvoVerseConfig(BaseSettings):
    llm: LLMConfig = LLMConfig()
    db: DatabaseConfig = DatabaseConfig()
    memory: MemoryConfig = MemoryConfig()
    neo4j: Neo4jConfig = Neo4jConfig()
    literature: LiteratureConfig = LiteratureConfig()
    knowledge: KnowledgeConfig = KnowledgeConfig()

    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "extra": "ignore"
    }


def get_config() -> EvoVerseConfig:
    return EvoVerseConfig()

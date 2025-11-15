"""
Knowledge and literature management for EvoVerse.

Provides:
- Paper embeddings (SPECTER)
- Vector database (ChromaDB)
- Semantic search
- Knowledge graph (Neo4j)
- Concept extraction (LLM)
- Graph building and visualization
"""

# Embeddings
from evoverse.knowledge.embeddings import (
    PaperEmbedder,
    get_embedder,
    reset_embedder
)

# Vector database
from evoverse.knowledge.vector_db import (
    PaperVectorDB,
    get_vector_db,
    reset_vector_db
)

# Semantic search
from evoverse.knowledge.semantic_search import (
    SemanticLiteratureSearch
)

# Knowledge graph
from evoverse.knowledge.graph import (
    KnowledgeGraph,
    get_knowledge_graph,
    reset_knowledge_graph
)

# Concept extraction
from evoverse.knowledge.concept_extractor import (
    ConceptExtractor,
    ExtractedConcept,
    ExtractedMethod,
    ConceptRelationship,
    ExtractionResult,
    get_concept_extractor,
    reset_concept_extractor
)

# Graph building
from evoverse.knowledge.graph_builder import (
    GraphBuilder,
    get_graph_builder,
    reset_graph_builder
)

# Graph visualization
from evoverse.knowledge.graph_visualizer import (
    GraphVisualizer,
    LayoutAlgorithm,
    VisualizationMode,
    get_graph_visualizer,
    reset_graph_visualizer
)

# Domain knowledge base (unified ontologies)
from evoverse.knowledge.domain_kb import (
    DomainKnowledgeBase,
    Domain,
    DomainConcept,
    CrossDomainMapping
)

__all__ = [
    # Embeddings
    "PaperEmbedder",
    "get_embedder",
    "reset_embedder",
    # Vector database
    "PaperVectorDB",
    "get_vector_db",
    "reset_vector_db",
    # Semantic search
    "SemanticLiteratureSearch",
    # Knowledge graph
    "KnowledgeGraph",
    "get_knowledge_graph",
    "reset_knowledge_graph",
    # Concept extraction
    "ConceptExtractor",
    "ExtractedConcept",
    "ExtractedMethod",
    "ConceptRelationship",
    "ExtractionResult",
    "get_concept_extractor",
    "reset_concept_extractor",
    # Graph building
    "GraphBuilder",
    "get_graph_builder",
    "reset_graph_builder",
    # Visualization
    "GraphVisualizer",
    "LayoutAlgorithm",
    "VisualizationMode",
    "get_graph_visualizer",
    "reset_graph_visualizer",
    # Domain knowledge base
    "DomainKnowledgeBase",
    "Domain",
    "DomainConcept",
    "CrossDomainMapping",
]

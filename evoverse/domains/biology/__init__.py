"""Biology domain module - metabolomics, genomics, and multi-modal integration

本模块原本依赖外部 `kosmos.domains.biology.*`，在 EvoVerse 中已经有等价实现，
因此这里改为从本地 `evoverse.domains.biology` 子模块中导入，避免对外部
`kosmos` 包的硬依赖。
"""

from .apis import (
    KEGGClient,
    GWASCatalogClient,
    GTExClient,
    ENCODEClient,
    dbSNPClient,
    EnsemblClient,
    HMDBClient,
    MetaboLightsClient,
    UniProtClient,
    PDBClient,
)

from .metabolomics import (
    MetabolomicsAnalyzer,
    MetabolomicsResult,
    PathwayPattern,
    PathwayComparison,
    MetaboliteCategory,
    MetaboliteType,
)

from .genomics import (
    GenomicsAnalyzer,
    GenomicsResult,
    CompositeScore,
    MechanismRanking,
    EvidenceLevel,
    EffectDirection,
)

from .ontology import (
    BiologyOntology,
    BiologicalConcept,
    BiologicalRelation,
    BiologicalRelationType,
)

__all__ = [
    # API Clients
    'KEGGClient',
    'GWASCatalogClient',
    'GTExClient',
    'ENCODEClient',
    'dbSNPClient',
    'EnsemblClient',
    'HMDBClient',
    'MetaboLightsClient',
    'UniProtClient',
    'PDBClient',

    # Metabolomics
    'MetabolomicsAnalyzer',
    'MetabolomicsResult',
    'PathwayPattern',
    'PathwayComparison',
    'MetaboliteCategory',
    'MetaboliteType',

    # Genomics
    'GenomicsAnalyzer',
    'GenomicsResult',
    'CompositeScore',
    'MechanismRanking',
    'EvidenceLevel',
    'EffectDirection',

    # Ontology
    'BiologyOntology',
    'BiologicalConcept',
    'BiologicalRelation',
    'BiologicalRelationType',
]

"""Neuroscience domain module - connectomics, neurodegeneration, and brain network analysis

原始版本依赖外部 `kosmos.domains.neuroscience.*`，在 EvoVerse 中已经有对应实现，
此处改为本地导入，消除对 kosmos 的硬依赖。
"""

from .apis import (
    FlyWireClient,
    AllenBrainClient,
    MICrONSClient,
    GEOClient,
    AMPADClient,
    OpenConnectomeClient,
    WormBaseClient,
    NeuronData,
    GeneExpressionData,
    ConnectomeDataset,
    DifferentialExpressionResult as APIDifferentialExpressionResult,
)

from .connectomics import (
    ConnectomicsAnalyzer,
    ConnectomicsResult,
    ScalingRelationship,
    PowerLawFit,
    CrossSpeciesComparison,
)

from .neurodegeneration import (
    NeurodegenerationAnalyzer,
    NeurodegenerationResult,
    DifferentialExpressionResult,
    PathwayEnrichmentResult,
    CrossSpeciesValidation,
    TemporalStage,
)

from .ontology import (
    NeuroscienceOntology,
)

__all__ = [
    # API Clients
    'FlyWireClient',
    'AllenBrainClient',
    'MICrONSClient',
    'GEOClient',
    'AMPADClient',
    'OpenConnectomeClient',
    'WormBaseClient',

    # API Data Models
    'NeuronData',
    'GeneExpressionData',
    'ConnectomeDataset',
    'APIDifferentialExpressionResult',

    # Connectomics
    'ConnectomicsAnalyzer',
    'ConnectomicsResult',
    'ScalingRelationship',
    'PowerLawFit',
    'CrossSpeciesComparison',

    # Neurodegeneration
    'NeurodegenerationAnalyzer',
    'NeurodegenerationResult',
    'DifferentialExpressionResult',
    'PathwayEnrichmentResult',
    'CrossSpeciesValidation',
    'TemporalStage',

    # Ontology
    'NeuroscienceOntology',
]

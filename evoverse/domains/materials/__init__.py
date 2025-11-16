"""Materials Science domain module - materials optimization and parameter analysis

原始实现依赖 `kosmos.domains.materials.*`，在 EvoVerse 中已经提供了本地版本，
这里改为从当前包的子模块导入，去掉对外部 kosmos 包的依赖。
"""

from .apis import (
    MaterialsProjectClient,
    NOMADClient,
    AflowClient,
    CitrinationClient,
    PerovskiteDBClient,
    MaterialProperties,
    NomadEntry,
    AflowMaterial,
    CitrinationData,
    PerovskiteExperiment,
)

from .optimization import (
    MaterialsOptimizer,
    CorrelationResult,
    SHAPResult,
    OptimizationResult,
    DOEResult,
)

from .ontology import (
    MaterialsOntology,
    MaterialsConcept,
    MaterialsRelation,
    MaterialsRelationType,
)

__all__ = [
    # API Clients
    'MaterialsProjectClient',
    'NOMADClient',
    'AflowClient',
    'CitrinationClient',
    'PerovskiteDBClient',

    # API Data Models
    'MaterialProperties',
    'NomadEntry',
    'AflowMaterial',
    'CitrinationData',
    'PerovskiteExperiment',

    # Optimization
    'MaterialsOptimizer',
    'CorrelationResult',
    'SHAPResult',
    'OptimizationResult',
    'DOEResult',

    # Ontology
    'MaterialsOntology',
    'MaterialsConcept',
    'MaterialsRelation',
    'MaterialsRelationType',
]

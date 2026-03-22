"""Extraction schemas package — one Pydantic model per clinical domain.

Re-exports every public symbol so that
``from info_extraction.schemas import ExtractionMetaDesign`` works.
"""

from typing import List, Type

from pydantic import BaseModel

from info_extraction.schemas._common import Image, ImageType
from info_extraction.schemas.diagnostic import ExtractionDiagnosticPerformance
from info_extraction.schemas.meta_design import ExtractionMetaDesign
from info_extraction.schemas.methods import ExtractionMethods
from info_extraction.schemas.outcomes import ExtractionOutcomes
from info_extraction.schemas.population import ExtractionPopulationIndications

# ── Single source of truth for all extraction schemas ──
EXTRACTION_SCHEMAS: List[Type[BaseModel]] = [
    ExtractionMetaDesign,
    ExtractionPopulationIndications,
    ExtractionMethods,
    ExtractionOutcomes,
    ExtractionDiagnosticPerformance,
]


def df_cols_from_model(model_cls: Type[BaseModel], use_alias: bool = True) -> List[str]:
    cols = []
    for name, field in model_cls.model_fields.items():
        col = field.alias if use_alias and getattr(field, "alias", None) else name
        cols.append(col)
    return cols


def df_cols_from_models(use_alias: bool = True) -> List[str]:
    seen: set[str] = set()
    out: list[str] = []
    for cls in EXTRACTION_SCHEMAS:
        for col in df_cols_from_model(cls, use_alias=use_alias):
            if col not in seen:
                seen.add(col)
                out.append(col)
    return out


__all__ = [
    "Image",
    "ImageType",
    "ExtractionMetaDesign",
    "ExtractionPopulationIndications",
    "ExtractionMethods",
    "ExtractionOutcomes",
    "ExtractionDiagnosticPerformance",
    "EXTRACTION_SCHEMAS",
    "df_cols_from_model",
    "df_cols_from_models",
]

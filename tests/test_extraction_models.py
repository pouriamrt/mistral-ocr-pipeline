"""Tests for Pydantic extraction models in info_extraction/extraction_payload.py."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from info_extraction.extraction_payload import (
    EXTRACTION_SCHEMAS,
    ExtractionDiagnosticPerformance,
    ExtractionMetaDesign,
    ExtractionMethods,
    ExtractionOutcomes,
    ExtractionPopulationIndications,
    df_cols_from_model,
    df_cols_from_models,
)

ALL_MODELS: list[type[BaseModel]] = [
    ExtractionMetaDesign,
    ExtractionPopulationIndications,
    ExtractionMethods,
    ExtractionOutcomes,
    ExtractionDiagnosticPerformance,
]


# ---------------------------------------------------------------------------
# Instantiation with defaults (no required fields crash)
# ---------------------------------------------------------------------------


class TestDefaultInstantiation:
    @pytest.mark.parametrize("model_cls", ALL_MODELS, ids=lambda m: m.__name__)
    def test_instantiate_with_defaults(self, model_cls: type[BaseModel]) -> None:
        """Every model should be constructible with zero arguments (all Optional)."""
        instance = model_cls()
        assert instance is not None


# ---------------------------------------------------------------------------
# model_config has populate_by_name=True
# ---------------------------------------------------------------------------


class TestModelConfig:
    @pytest.mark.parametrize("model_cls", ALL_MODELS, ids=lambda m: m.__name__)
    def test_populate_by_name_enabled(self, model_cls: type[BaseModel]) -> None:
        config = model_cls.model_config
        assert config.get("populate_by_name") is True


# ---------------------------------------------------------------------------
# df_cols_from_model / df_cols_from_models
# ---------------------------------------------------------------------------


class TestDfCols:
    @pytest.mark.parametrize("model_cls", ALL_MODELS, ids=lambda m: m.__name__)
    def test_df_cols_from_model_non_empty(self, model_cls: type[BaseModel]) -> None:
        cols = df_cols_from_model(model_cls)
        assert len(cols) > 0

    def test_df_cols_from_models_non_empty_no_duplicates(self) -> None:
        cols = df_cols_from_models()
        assert len(cols) > 0
        assert len(cols) == len(set(cols)), "df_cols_from_models returned duplicates"


# ---------------------------------------------------------------------------
# EXTRACTION_SCHEMAS
# ---------------------------------------------------------------------------


class TestExtractionSchemas:
    def test_exactly_five_entries(self) -> None:
        assert len(EXTRACTION_SCHEMAS) == 5

    @pytest.mark.parametrize("schema_cls", EXTRACTION_SCHEMAS, ids=lambda m: m.__name__)
    def test_is_basemodel_subclass(self, schema_cls: type[BaseModel]) -> None:
        assert issubclass(schema_cls, BaseModel)


# ---------------------------------------------------------------------------
# Representative data round-trip
# ---------------------------------------------------------------------------


class TestRepresentativeData:
    def test_meta_design_with_real_data(self) -> None:
        instance = ExtractionMetaDesign(
            journal="Lancet",
            title="A Randomized Trial of Apixaban",
            publication_year="2022",
            study_design="Randomized Controlled Trial",
        )
        assert instance.journal == "Lancet"
        assert instance.title == "A Randomized Trial of Apixaban"
        assert instance.publication_year == "2022"
        assert instance.study_design == "Randomized Controlled Trial"


# ---------------------------------------------------------------------------
# Alias round-trip
# ---------------------------------------------------------------------------


class TestAliasRoundTrip:
    def test_create_with_alias_dump_with_alias(self) -> None:
        instance = ExtractionMetaDesign(
            **{
                "Journal": "Lancet",
                "Title": "Test Title",
                "Publication Year": "2023",
            }
        )
        dumped = instance.model_dump(by_alias=True)
        assert "Journal" in dumped
        assert "Title" in dumped
        assert "Publication Year" in dumped
        assert dumped["Journal"] == "Lancet"


# ---------------------------------------------------------------------------
# Paired-field invariant: every *_sentence_from_text has a matching base field
# ---------------------------------------------------------------------------


class TestPairedFieldInvariant:
    SUFFIX = "_sentence_from_text"

    @pytest.mark.parametrize("model_cls", ALL_MODELS, ids=lambda m: m.__name__)
    def test_sentence_from_text_fields_have_base_field(
        self, model_cls: type[BaseModel]
    ) -> None:
        field_names = set(model_cls.model_fields.keys())
        sentence_fields = [f for f in field_names if f.endswith(self.SUFFIX)]
        for sf in sentence_fields:
            base = sf.removesuffix(self.SUFFIX)
            # Some base fields use a `_flat` suffix (e.g. clinical_outcome_followup_flat)
            has_match = base in field_names or (base + "_flat") in field_names
            assert has_match, (
                f"Model {model_cls.__name__}: '{sf}' has no matching base field "
                f"'{base}' or '{base}_flat'"
            )

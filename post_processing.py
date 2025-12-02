from dataclasses import dataclass
from typing import List, Any, Optional

import json
import pandas as pd
from tqdm import tqdm

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI


# ------------------------------
# Config for which fields to check
# ------------------------------


@dataclass
class FieldValidationConfig:
    # Column that contains the extracted value(s)
    value_field: str
    # Column that contains the supporting sentence(s)
    sentence_field: str
    # True if the value is a list (multi-label); False for scalar
    is_list: bool = True
    # Name/description of this field for the LLM
    field_label: str = ""
    # Optional: if you want the LLM to be slightly more lenient/strict later
    required_strength: str = "clear"


# Example configs – adapt to your exact column names
DEFAULT_FIELD_CONFIGS: List[FieldValidationConfig] = [
    FieldValidationConfig(
        value_field="DOAC Level Measurement",
        sentence_field="DOAC Level Measurement Sentence from Text",
        is_list=True,
        field_label="DOAC level measurement methods",
    ),
    FieldValidationConfig(
        value_field="Clinical Outcomes",
        sentence_field="Clinical Outcomes Sentence from Text",
        is_list=True,
        field_label="clinical outcomes",
    ),
    FieldValidationConfig(
        value_field="Patient population 3",  # relevant_subgroups
        sentence_field="Relevant Subgroups Sentence from Text",
        is_list=True,
        field_label="relevant patient subgroups",
    ),
    # add more configs as needed ...
]


# ------------------------------
# LLM validator chain
# ------------------------------


def make_validator_chain(model: Optional[Runnable] = None) -> Runnable:
    """
    Create an LLM chain that, given a field name, extracted values, and supporting sentences,
    returns JSON with booleans indicating whether each value is supported by the sentence.
    """
    if model is None:
        # You can tweak temperature / model here
        model = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.0,
        )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a strict scientific validator. Your job is to check whether "
                    "specific extracted values are REALLY supported by the evidence sentences.\n\n"
                    "Rules:\n"
                    "1. Only use the provided sentences as evidence; ignore any outside knowledge.\n"
                    "2. A value is SUPPORTED only if the sentence clearly states that this value "
                    "applies to THIS study's own patients/measurements.\n"
                    "3. If the sentence is background, refers to other studies, guidelines, or "
                    "general statements (not specifically 'we measured', 'in this study', etc.), "
                    "then the value is NOT supported.\n"
                    "4. When unsure, mark the value as not supported.\n\n"
                    "Output STRICT JSON with booleans as described."
                ),
            ),
            (
                "user",
                (
                    "Field name: {field_label}\n"
                    "Row identifier: {row_id}\n\n"
                    "Extracted values (as a JSON array or scalar):\n"
                    "{values_json}\n\n"
                    "Supporting sentences (same order, JSON array or scalar):\n"
                    "{sentences_json}\n\n"
                    "For each value, decide if it is supported by its corresponding sentence.\n"
                    "Respond ONLY with JSON of the form:\n"
                    "{{\n"
                    '  "is_list": true | false,\n'
                    '  "supported": [true/false or single bool],\n'
                    '  "notes": "short explanation if needed"\n'
                    "}}\n"
                ),
            ),
        ]
    )

    parser = JsonOutputParser()
    chain = prompt | model | parser
    return chain


# ------------------------------
# Row-level validation logic
# ------------------------------


def _normalize_scalar_or_list(v: Any, expect_list: bool) -> List[Any] | Any:
    """
    Ensure values and sentences are in compatible shapes.
    """
    if v is None:
        return [] if expect_list else None
    if expect_list:
        if isinstance(v, list):
            return v
        # sometimes they come in as a stringified list
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        return [v]
    else:
        # scalar expected
        if isinstance(v, list):
            # keep first non-null-ish element
            for item in v:
                if item not in (None, "", [], {}):
                    return item
            return None
        return v


def validate_field_with_llm(
    row: pd.Series,
    cfg: FieldValidationConfig,
    chain: Runnable,
    row_id: Any,
) -> pd.Series:
    """
    Validate one field in one row with the LLM, updating the row in-place.
    """
    values_raw = row.get(cfg.value_field)
    sentences_raw = row.get(cfg.sentence_field)

    # If value is empty, nothing to do
    if values_raw in (None, "", [], {}):
        return row

    values = _normalize_scalar_or_list(values_raw, cfg.is_list)
    sentences = _normalize_scalar_or_list(sentences_raw, cfg.is_list)

    # If we don't have sentences, we can't validate – keep as-is
    if sentences in (None, "", [], {}):
        return row

    # For lists, lengths must match for 1:1 mapping; if not, leave as-is
    if cfg.is_list and isinstance(values, list) and isinstance(sentences, list):
        if len(values) != len(sentences):
            # optional: log somewhere; for now, skip validation
            return row

    # Prepare JSON for the LLM
    values_json = json.dumps(values, ensure_ascii=False)
    sentences_json = json.dumps(sentences, ensure_ascii=False)

    try:
        result = chain.invoke(
            {
                "field_label": cfg.field_label or cfg.value_field,
                "row_id": str(row_id),
                "values_json": values_json,
                "sentences_json": sentences_json,
            }
        )
    except Exception as e:
        # If LLM fails, keep original
        print(
            f"[WARN] LLM validation failed for field '{cfg.value_field}' row {row_id}: {e}"
        )
        return row

    supported = result.get("supported")

    if cfg.is_list:
        if not isinstance(values, list) or not isinstance(supported, list):
            return row
        if len(values) != len(supported):
            return row

        # Filter out unsupported items
        new_values = []
        new_sentences = []
        for v, s, ok in zip(values, sentences, supported):
            if ok:
                new_values.append(v)
                new_sentences.append(s)

        if new_values:
            row[cfg.value_field] = new_values
            row[cfg.sentence_field] = new_sentences
        else:
            row[cfg.value_field] = None
            row[cfg.sentence_field] = None

    else:
        # scalar case
        if isinstance(supported, list):
            # take first if provided oddly
            supported = bool(supported[0]) if supported else False
        if not supported:
            row[cfg.value_field] = None
            row[cfg.sentence_field] = None

    return row


def validate_dataframe_with_llm(
    df: pd.DataFrame,
    field_configs: List[FieldValidationConfig] | None = None,
    model: Optional[Runnable] = None,
) -> pd.DataFrame:
    """
    Run LLM-based validation over all rows and configured fields.
    Returns a new DataFrame with invalid values nulled out.
    """
    if field_configs is None:
        field_configs = DEFAULT_FIELD_CONFIGS

    chain = make_validator_chain(model=model)

    df_validated = df.copy()
    for cfg in field_configs:
        missing_cols = [
            c
            for c in [cfg.value_field, cfg.sentence_field]
            if c not in df_validated.columns
        ]
        if missing_cols:
            print(
                f"[INFO] Skipping field '{cfg.value_field}' – missing columns: {missing_cols}"
            )
            continue

        print(f"[INFO] Validating field '{cfg.value_field}' using LLM...")
        rows = []
        for idx, row in tqdm(df_validated.iterrows(), total=len(df_validated)):
            row = validate_field_with_llm(row, cfg, chain, row_id=idx)
            rows.append(row)

        df_validated = pd.DataFrame(rows)

    return df_validated

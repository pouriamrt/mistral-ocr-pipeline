from typing import List, Any, Optional

import json
import os
from math import ceil
import ast

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from unstack_payloads import get_all_field_configs, FieldValidationConfig


load_dotenv(override=True)

MODEL = os.getenv("MODEL_JUDGE", "gpt-5-mini")

# ------------------------------
# Config for which fields to check
# ------------------------------

DEFAULT_FIELD_CONFIGS = get_all_field_configs()


# ------------------------------
# LLM validator chain
# ------------------------------


def make_validator_chain(model: Optional[Runnable] = None) -> Runnable:
    """
    Create an LLM chain that, given a field name, extracted values, and supporting sentences,
    returns JSON with booleans indicating whether each value is supported by the sentence.
    """
    if model is None:
        model = ChatOpenAI(
            model=MODEL,
            temperature=0.0,
        )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a scientific validator. Your job is to check whether "
                    "specific extracted values are REALLY supported by the evidence sentences.\n\n"
                    "Rules:\n"
                    "1. Only use the provided sentences as evidence; ignore any outside knowledge.\n"
                    "2. A value is SUPPORTED only if the sentence clearly states that this value "
                    "applies to THIS study's own patients/measurements.\n"
                    "3. If the sentence is background, refers to other studies, guidelines, or "
                    "general statements (not specifically 'we measured', 'in this study', etc.), "
                    "then the value is NOT supported.\n\n"
                    "Output JSON with booleans as described."
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
                    "For each value, decide if it is supported by its corresponding sentence. "
                    "If values and sentences are lists, check value[i] against sentence[i] for each index i.\n"
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
# Normalization helpers
# ------------------------------


def _normalize_scalar_or_list(v: Any, expect_list: bool) -> List[Any] | Any:
    """
    Ensure values and sentences are in compatible shapes.
    Also handles Python-list-like strings such as "['a', 'b']".
    """
    if v is None:
        return [] if expect_list else None

    if expect_list:
        if isinstance(v, list):
            return v

        if isinstance(v, str):
            try:
                parsed = ast.literal_eval(v)
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

        if isinstance(v, str):
            try:
                parsed = ast.literal_eval(v)
                if not isinstance(parsed, list):
                    return parsed
            except Exception:
                pass

        return v


def _apply_llm_result_to_row(
    row: pd.Series,
    cfg: FieldValidationConfig,
    values: Any,
    sentences: Any,
    result: dict,
) -> pd.Series:
    """
    Given an LLM result JSON for one row and field, return a copy of the row
    with sentences kept and unsupported values removed/nulled out.
    """
    supported = result.get("supported")
    row_copy = row.copy()

    if cfg.is_list:
        if not isinstance(values, list) or not isinstance(sentences, list):
            return row_copy
        if not isinstance(supported, list):
            return row_copy
        if len(values) != len(sentences) or len(values) != len(supported):
            return row_copy

        # Keep all sentences unchanged, but filter out unsupported values
        # Filter out None values to avoid ['None'] in output
        filtered_values = []
        for v, ok in zip(values, supported):
            # Only keep the value if it's supported
            if ok:
                filtered_values.append(v)

        # Set to empty list if all values were filtered out, otherwise use filtered list
        # Keep sentences unchanged as requested
        row_copy[cfg.value_field] = filtered_values if filtered_values else None
        row_copy[cfg.sentence_field] = sentences if sentences else None

    else:
        # scalar case
        if isinstance(supported, list):
            # take first if provided oddly
            supported = bool(supported[0]) if supported else False

        # Always keep the sentence for scalar case
        # Only remove the value if not supported
        if not supported:
            row_copy[cfg.value_field] = None
        # Keep the sentence field as-is

    return row_copy


# ------------------------------
# DataFrame-level batched validation
# ------------------------------


def validate_dataframe_with_llm(
    df: pd.DataFrame,
    field_configs: List[FieldValidationConfig] | None = None,
    model: Optional[Runnable] = None,
    batch_size: int = 16,
) -> pd.DataFrame:
    """
    Run LLM-based validation over all rows and configured fields, using batched
    LLM calls (chain.batch).

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

        print(f"[INFO] Validating field '{cfg.value_field}' using LLM (batched)...")

        # Build inputs and metadata for rows that actually need validation
        inputs = []  # list of dicts to feed into chain.batch
        meta = []  # parallel list: (row_index, values, sentences)

        for idx, row in df_validated.iterrows():
            values_raw = row.get(cfg.value_field)
            sentences_raw = row.get(cfg.sentence_field)

            # If value is empty, nothing to do
            if values_raw in (None, "", [], {}):
                continue

            values = _normalize_scalar_or_list(values_raw, cfg.is_list)
            sentences = _normalize_scalar_or_list(sentences_raw, cfg.is_list)

            # If we don't have sentences, we can't validate – keep as-is
            if sentences in (None, "", [], {}):
                continue

            # For lists, lengths must match for 1:1 mapping; if not, leave as-is
            if cfg.is_list and isinstance(values, list) and isinstance(sentences, list):
                if len(values) != len(sentences):
                    # skip this row for validation
                    continue

            values_json = json.dumps(values, ensure_ascii=False)
            sentences_json = json.dumps(sentences, ensure_ascii=False)

            inputs.append(
                {
                    "field_label": cfg.field_label or cfg.value_field,
                    "row_id": str(idx),
                    "values_json": values_json,
                    "sentences_json": sentences_json,
                }
            )
            meta.append((idx, values, sentences))

        if not inputs:
            # nothing to validate for this field
            continue

        total = len(inputs)
        num_batches = ceil(total / batch_size)
        all_results: List[Optional[dict]] = []

        for b in tqdm(
            range(num_batches),
            desc=f"LLM batches for {cfg.value_field}",
        ):
            start = b * batch_size
            end = min((b + 1) * batch_size, total)
            batch_inputs = inputs[start:end]

            try:
                batch_results = chain.batch(batch_inputs)
            except Exception as e:
                print(
                    f"[WARN] LLM batch failed for field '{cfg.value_field}' "
                    f"batch {b + 1}/{num_batches}: {e}"
                )
                # Fill with None so lengths stay aligned
                batch_results = [None] * len(batch_inputs)

            all_results.extend(batch_results)

        # Apply results back to df_validated
        for (idx, values, sentences), result in zip(meta, all_results):
            if result is None:
                # skip this row on error
                continue
            row = df_validated.loc[idx]
            row = _apply_llm_result_to_row(row, cfg, values, sentences, result)
            df_validated.loc[idx] = row

    return df_validated


if __name__ == "__main__":
    df = pd.read_csv("output/aggregated/df_annotations.csv")
    # df = df.iloc[:10]
    df_validated = validate_dataframe_with_llm(df, batch_size=16)
    df_validated.to_csv(
        "output/aggregated/df_annotations_validated.csv",
        index=False,
    )

from dataclasses import dataclass
from typing import Any, Union, get_origin, get_args
from pydantic import BaseModel

from info_extraction.extraction_payload import EXTRACTION_SCHEMAS


# -------------------------------------------------
# FieldValidationConfig dataclass
# -------------------------------------------------
@dataclass
class FieldValidationConfig:
    value_field: str
    sentence_field: str
    is_list: bool = True
    field_label: str = ""
    required_strength: str = "clear"


# -------------------------------------------------
# Helper to detect list-like annotations
# -------------------------------------------------
def _is_list_type(annotation: Any) -> bool:
    """
    Determine if a field's annotation is a list[...] (optionally wrapped in Optional).
    """
    origin = get_origin(annotation)

    if origin is list:
        return True

    # Optional[List[...]] is Union[List[...], NoneType]
    if origin is Union:
        return any(get_origin(a) is list for a in get_args(annotation))

    return False


# -------------------------------------------------
# Core builder: from a single Pydantic model
# -------------------------------------------------
def build_field_configs_for_model(
    model: type[BaseModel],
    label_overrides: dict[str, str] | None = None,
    sentence_suffix: str = "_sentence_from_text",
) -> list[FieldValidationConfig]:
    """
    Build FieldValidationConfig entries for a Pydantic model.

    Rules:
    - For every field ending with `sentence_suffix`, look for a matching
      value field with the same base name.
    - Use the Pydantic field alias as `value_field` / `sentence_field`.
    - `is_list` is True if the value field is (optionally) a List[…].
    - `field_label` is taken from `label_overrides` if present, otherwise
      it is a simple lowercased version of the value field alias.
    """
    label_overrides = label_overrides or {}

    configs: list[FieldValidationConfig] = []
    fields = model.model_fields  # pydantic v2

    for name, sentence_field in fields.items():
        # Only consider fields that represent "Sentence from Text"
        if not name.endswith(sentence_suffix):
            continue

        base_name = name[: -len(sentence_suffix)]
        if base_name not in fields:
            # No matching value field, skip
            continue

        value_field = fields[base_name]

        value_alias = value_field.alias or base_name
        sentence_alias = sentence_field.alias or name

        is_list = _is_list_type(value_field.annotation)

        # Choose label:
        # 1) explicit override by internal field name
        # 2) otherwise, lowercase alias
        field_label = label_overrides.get(
            base_name,
            value_alias.lower(),
        )

        configs.append(
            FieldValidationConfig(
                value_field=value_alias,
                sentence_field=sentence_alias,
                is_list=is_list,
                field_label=field_label,
            )
        )

    return configs


# -------------------------------------------------
# Get all field configs
# -------------------------------------------------
def get_all_field_configs() -> list[FieldValidationConfig]:
    configs: list[FieldValidationConfig] = []
    for schema in EXTRACTION_SCHEMAS:
        configs.extend(build_field_configs_for_model(schema))
    return configs


if __name__ == "__main__":
    DEFAULT_FIELD_CONFIGS = get_all_field_configs()

    print(DEFAULT_FIELD_CONFIGS, len(DEFAULT_FIELD_CONFIGS))

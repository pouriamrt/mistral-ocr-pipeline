"""Tests for merge_dicts and _merge_values from utils/utils.py."""

from __future__ import annotations

from utils.utils import merge_dicts


# ---------------------------------------------------------------------------
# Basic merging
# ---------------------------------------------------------------------------


class TestBasicMerging:
    def test_empty_list_returns_empty_dict(self) -> None:
        assert merge_dicts([]) == {}

    def test_single_dict_returns_copy(self) -> None:
        original = {"a": 1, "b": 2}
        result = merge_dicts([original])
        assert result == {"a": 1, "b": 2}
        # Must be a copy, not the same object
        assert result is not original

    def test_non_overlapping_keys_union(self) -> None:
        result = merge_dicts([{"a": 1}, {"b": 2}])
        assert result == {"a": 1, "b": 2}

    def test_overlapping_scalar_keys_first_wins(self) -> None:
        result = merge_dicts([{"a": "first"}, {"a": "second"}])
        assert result == {"a": "first"}


# ---------------------------------------------------------------------------
# Empty / None handling
# ---------------------------------------------------------------------------


class TestEmptyNoneHandling:
    def test_none_a_data_b_returns_b(self) -> None:
        result = merge_dicts([{"a": None}, {"a": "data"}])
        assert result["a"] == "data"

    def test_empty_string_a_data_b_returns_b(self) -> None:
        result = merge_dicts([{"a": ""}, {"a": "data"}])
        assert result["a"] == "data"

    def test_empty_list_a_data_b_returns_b(self) -> None:
        result = merge_dicts([{"a": []}, {"a": [1, 2]}])
        assert result["a"] == [1, 2]

    def test_data_a_none_b_returns_a(self) -> None:
        result = merge_dicts([{"a": "data"}, {"a": None}])
        assert result["a"] == "data"

    def test_both_none_returns_none(self) -> None:
        result = merge_dicts([{"a": None}, {"a": None}])
        assert result["a"] is None


# ---------------------------------------------------------------------------
# List merging with dedup
# ---------------------------------------------------------------------------


class TestListMerging:
    def test_no_overlap_concatenated(self) -> None:
        result = merge_dicts([{"a": [1, 2]}, {"a": [3, 4]}])
        assert result["a"] == [1, 2, 3, 4]

    def test_duplicates_deduped(self) -> None:
        result = merge_dicts([{"a": [1, 2, 3]}, {"a": [2, 3, 4]}])
        assert result["a"] == [1, 2, 3, 4]

    def test_dict_items_deduped_same_order(self) -> None:
        result = merge_dicts([{"a": [{"x": 1}]}, {"a": [{"x": 1}]}])
        assert result["a"] == [{"x": 1}]

    def test_dict_items_deduped_different_key_order(self) -> None:
        """Regression test: dicts with different key order should still dedup
        because _merge_values uses json.dumps(sort_keys=True)."""
        result = merge_dicts([{"a": [{"x": 1, "y": 2}]}, {"a": [{"y": 2, "x": 1}]}])
        assert result["a"] == [{"x": 1, "y": 2}]


# ---------------------------------------------------------------------------
# Nested dict merging
# ---------------------------------------------------------------------------


class TestNestedDictMerging:
    def test_nested_dicts_recursive(self) -> None:
        d1 = {"outer": {"a": 1}}
        d2 = {"outer": {"b": 2}}
        result = merge_dicts([d1, d2])
        assert result == {"outer": {"a": 1, "b": 2}}

    def test_nested_dicts_and_lists(self) -> None:
        d1 = {"outer": {"items": [1, 2], "name": "foo"}}
        d2 = {"outer": {"items": [2, 3], "extra": True}}
        result = merge_dicts([d1, d2])
        assert result["outer"]["items"] == [1, 2, 3]
        assert result["outer"]["name"] == "foo"
        assert result["outer"]["extra"] is True


# ---------------------------------------------------------------------------
# String normalisation
# ---------------------------------------------------------------------------


class TestStringNormalization:
    def test_whitespace_stripped(self) -> None:
        result = merge_dicts([{"a": "  hello  "}, {"a": "world"}])
        assert result["a"] == "hello"

    def test_whitespace_string_wins_over_none(self) -> None:
        result = merge_dicts([{"a": " hello "}, {"a": None}])
        assert result["a"] == "hello"


# ---------------------------------------------------------------------------
# Multi-dict merging
# ---------------------------------------------------------------------------


class TestMultiDictMerging:
    def test_three_dicts_merged_progressively(self) -> None:
        result = merge_dicts([{"a": 1}, {"b": 2}, {"c": 3}])
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_mixed_scalars_lists_nested_across_three_dicts(self) -> None:
        d1 = {"name": "first", "tags": ["a"], "meta": {"k1": "v1"}}
        d2 = {"name": None, "tags": ["b"], "meta": {"k2": "v2"}}
        d3 = {"name": "", "tags": ["a", "c"], "meta": {"k3": "v3"}}
        result = merge_dicts([d1, d2, d3])
        assert result["name"] == "first"
        assert result["tags"] == ["a", "b", "c"]
        assert result["meta"] == {"k1": "v1", "k2": "v2", "k3": "v3"}

"""Tests for resume-index helpers in utils/utils.py:
- file_name_sha1
- load_existing_index
- drop_empty_rows
- append_csv_row
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.utils import (
    append_csv_row,
    drop_empty_rows,
    file_name_sha1,
    load_existing_index,
)


# ---------------------------------------------------------------------------
# file_name_sha1
# ---------------------------------------------------------------------------


class TestFileNameSha1:
    def test_consistent_hash(self) -> None:
        h1 = file_name_sha1("paper.pdf")
        h2 = file_name_sha1("paper.pdf")
        assert h1 == h2

    def test_different_names_different_hashes(self) -> None:
        h1 = file_name_sha1("paper_a.pdf")
        h2 = file_name_sha1("paper_b.pdf")
        assert h1 != h2


# ---------------------------------------------------------------------------
# load_existing_index
# ---------------------------------------------------------------------------


class TestLoadExistingIndex:
    def test_nonexistent_file_returns_empty_set(self, tmp_path: Path) -> None:
        result = load_existing_index(tmp_path / "does_not_exist.csv")
        assert result == set()

    def test_returns_set_of_source_file_hashes(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "index.csv"
        df = pd.DataFrame(
            {
                "__source_file__": ["hash_a", "hash_b", "hash_c"],
                "Journal": ["Lancet", "BMJ", "NEJM"],
            }
        )
        df.to_csv(csv_path, index=False)
        result = load_existing_index(csv_path)
        assert result == {"hash_a", "hash_b", "hash_c"}


# ---------------------------------------------------------------------------
# drop_empty_rows
# ---------------------------------------------------------------------------


class TestDropEmptyRows:
    def test_removes_nan_source_file(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame(
            {
                "__source_file__": ["hash_a", None, "hash_c"],
                "Journal": ["Lancet", "BMJ", "NEJM"],
            }
        )
        df.to_csv(csv_path, index=False)
        drop_empty_rows(csv_path)
        result = pd.read_csv(csv_path)
        assert len(result) == 2
        assert set(result["__source_file__"]) == {"hash_a", "hash_c"}

    def test_removes_numeric_journal(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame(
            {
                "__source_file__": ["h1", "h2", "h3"],
                "Journal": ["123", "45.6", "Lancet"],
            }
        )
        df.to_csv(csv_path, index=False)
        drop_empty_rows(csv_path)
        result = pd.read_csv(csv_path)
        assert len(result) == 1
        assert result.iloc[0]["Journal"] == "Lancet"

    def test_keeps_text_journal(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame(
            {
                "__source_file__": ["h1", "h2"],
                "Journal": ["Lancet", "BMJ"],
            }
        )
        df.to_csv(csv_path, index=False)
        drop_empty_rows(csv_path)
        result = pd.read_csv(csv_path)
        assert len(result) == 2

    def test_handles_missing_journal_column(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame({"__source_file__": ["h1", "h2"], "other": [1, 2]})
        df.to_csv(csv_path, index=False)
        # Should not raise
        drop_empty_rows(csv_path)
        result = pd.read_csv(csv_path)
        assert len(result) == 2

    def test_handles_missing_source_file_column(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame({"Journal": ["Lancet", "BMJ"], "other": [1, 2]})
        df.to_csv(csv_path, index=False)
        # Should not raise
        drop_empty_rows(csv_path)
        result = pd.read_csv(csv_path)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# append_csv_row
# ---------------------------------------------------------------------------


class TestAppendCsvRow:
    def test_creates_new_csv_with_header(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "output.csv"
        cols = ["a", "b", "c"]
        row = {"a": 1, "b": 2, "c": 3}
        append_csv_row(csv_path, row, cols)
        result = pd.read_csv(csv_path)
        assert list(result.columns) == cols
        assert len(result) == 1
        assert result.iloc[0]["a"] == 1

    def test_appends_without_duplicating_header(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "output.csv"
        cols = ["a", "b", "c"]
        append_csv_row(csv_path, {"a": 1, "b": 2, "c": 3}, cols)
        append_csv_row(csv_path, {"a": 4, "b": 5, "c": 6}, cols)
        result = pd.read_csv(csv_path)
        assert list(result.columns) == cols
        assert len(result) == 2
        assert result.iloc[1]["a"] == 4

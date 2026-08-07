"""
Tests for odm_linkmlgen.utils.general_utils, the shared DataFrame helpers.

The I/O functions (extract_sheets, save_data_frame, read_data_frame, clear_dirs)
are not covered here, since they touch the filesystem.
"""

import pandas as pd

from odm_linkmlgen.utils.general_utils import (
    choose_ignore_case_value,
    expand_multi_rows,
    get_class_name_from_file_name,
    order_columns,
    rename_items,
    strip_whitespace,
)

# --- order_columns ---


def test_order_columns_reorders():
    df = pd.DataFrame({"b": [1], "a": [2], "c": [3]})
    result = order_columns(df, ["a", "b"])
    assert list(result.columns) == ["a", "b", "c"]


def test_order_columns_df_columns_not_in_order_appended():
    df = pd.DataFrame({"b": [1], "a": [2], "z": [3]})
    result = order_columns(df, ["a", "b"])
    assert list(result.columns) == ["a", "b", "z"]


def test_order_columns_returns_copy():
    df = pd.DataFrame({"a": [1], "b": [2]})
    result = order_columns(df, ["b", "a"])
    result["a"] = 99
    assert df["a"].iloc[0] == 1


# --- strip_whitespace ---


def test_strip_whitespace_trims_strings():
    df = pd.DataFrame({"a": ["  hello  ", " world "], "b": [1, 2]})
    result = strip_whitespace(df)
    assert result["a"].tolist() == ["hello", "world"]
    assert result["b"].tolist() == [1, 2]


def test_strip_whitespace_ignores_non_strings():
    df = pd.DataFrame({"a": [1.5, None]})
    result = strip_whitespace(df)
    assert result["a"].tolist()[0] == 1.5


# --- expand_multi_rows ---


def test_expand_multi_rows_single_column():
    df = pd.DataFrame({"name": ["a;b;c"], "val": ["x"]})
    result = expand_multi_rows(df, "name")
    assert result["name"].tolist() == ["a", "b", "c"]
    assert result["val"].tolist() == ["x", "x", "x"]


def test_expand_multi_rows_multiple_columns():
    df = pd.DataFrame({"name": ["a;b"], "color": ["red;blue"]})
    result = expand_multi_rows(df, ["name", "color"])
    assert result["name"].tolist() == ["a", "b"]
    assert result["color"].tolist() == ["red", "blue"]


def test_expand_multi_rows_shorter_column_repeats_last():
    df = pd.DataFrame({"name": ["a;b;c"], "color": ["red;blue"]})
    result = expand_multi_rows(df, ["name", "color"])
    assert len(result) == 3
    assert result["color"].tolist() == ["red", "blue", "blue"]


def test_expand_multi_rows_no_separator_unchanged():
    df = pd.DataFrame({"name": ["abc"], "val": ["x"]})
    result = expand_multi_rows(df, "name")
    assert len(result) == 1
    assert result["name"].iloc[0] == "abc"


def test_expand_multi_rows_original_unchanged():
    df = pd.DataFrame({"name": ["a;b"]})
    expand_multi_rows(df, "name")
    assert df["name"].iloc[0] == "a;b"


# --- rename_items ---


def test_rename_items_renames_target():
    assert rename_items(["a", "b", "c"], {"b": "B"}) == ["a", "B", "c"]


def test_rename_items_original_unchanged():
    original = ["a", "b", "c"]
    rename_items(original, {"b": "B"})
    assert original == ["a", "b", "c"]


def test_rename_items_multiple_renames():
    assert rename_items(["a", "b", "c"], {"a": "A", "c": "C"}) == ["A", "b", "C"]


# --- choose_ignore_case_value ---


def test_choose_ignore_case_value_matches_lowercase():
    assert choose_ignore_case_value("HELLO", ["hello", "world"]) == "hello"


def test_choose_ignore_case_value_exact_match():
    assert choose_ignore_case_value("hello", ["hello", "world"]) == "hello"


def test_choose_ignore_case_value_no_match_returns_original():
    assert choose_ignore_case_value("xyz", ["hello", "world"]) == "xyz"


def test_choose_ignore_case_value_no_match_returns_none():
    result = choose_ignore_case_value("xyz", ["hello"], return_same_if_missing=False)
    assert result is None


def test_choose_ignore_case_value_non_string_passthrough():
    assert choose_ignore_case_value(42, ["hello"]) == 42


# --- get_class_name_from_file_name ---


def test_get_class_name_from_file_name_simple():
    assert get_class_name_from_file_name("samples.csv") == "samples"


def test_get_class_name_from_file_name_with_brackets():
    assert get_class_name_from_file_name("samples[extra_info].csv") == "samples"


def test_get_class_name_from_file_name_with_path():
    assert get_class_name_from_file_name("/path/to/measures.tsv") == "measures"

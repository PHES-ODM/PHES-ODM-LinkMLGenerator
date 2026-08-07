"""
Tests for odm_linkmlgen.nwss.nwss_utils.splitup_metadata_sheet, which splits a
flat NWSS metadata sheet into one DataFrame per table.
"""

import pandas as pd
import pytest

from odm_linkmlgen.nwss.nwss_utils import (
    SINGLE_TABLE_NAME,
    TABLE_NAME_COL,
    DictionaryColumns,
    splitup_metadata_sheet,
)


def _boundary_row(table_name: str) -> dict:
    """A table-boundary row: table name in Field Name, NaN (None) in Data Type."""
    return {DictionaryColumns.FIELD_NAME: table_name, DictionaryColumns.DATA_TYPE: None}


def _data_row(field_name: str, data_type: str = "string") -> dict:
    """A regular (non-boundary) row: a field name and a non-empty Data Type."""
    return {
        DictionaryColumns.FIELD_NAME: field_name,
        DictionaryColumns.DATA_TYPE: data_type,
    }


def _make_metadata_df(*table_defs) -> pd.DataFrame:
    """Build a metadata sheet from alternating (table_name, [data_rows]) pairs."""
    rows = []
    for table_name, data_rows in table_defs:
        rows.append(_boundary_row(table_name))
        rows.extend(data_rows)
    return pd.DataFrame(rows)


# --- splitup_metadata_sheet ---


def test_splitup_two_tables():
    df = _make_metadata_df(
        ("tableA", [_data_row("field1")]),
        ("tableB", [_data_row("field2"), _data_row("field3")]),
    )
    result = splitup_metadata_sheet(df)
    assert set(result.keys()) == {"tableA", "tableB"}
    assert len(result["tableA"]) == 1
    assert len(result["tableB"]) == 2


def test_splitup_adds_table_name_col():
    df = _make_metadata_df(("myTable", [_data_row("f1")]))
    result = splitup_metadata_sheet(df)
    assert result["myTable"][TABLE_NAME_COL].iloc[0] == "myTable"


def test_splitup_single_table_flag_merges_all():
    df = _make_metadata_df(
        ("tableA", [_data_row("f1"), _data_row("f2")]),
        ("tableB", [_data_row("f3")]),
    )
    result = splitup_metadata_sheet(df, single_table=True)
    assert list(result.keys()) == [SINGLE_TABLE_NAME]
    assert len(result[SINGLE_TABLE_NAME]) == 3


def test_splitup_single_table_sets_table_name_col():
    df = _make_metadata_df(("tableA", [_data_row("f1")]))
    result = splitup_metadata_sheet(df, single_table=True)
    assert result[SINGLE_TABLE_NAME][TABLE_NAME_COL].iloc[0] == SINGLE_TABLE_NAME


def test_splitup_duplicate_table_name_raises():
    df = _make_metadata_df(
        ("tableA", [_data_row("f1")]),
        ("tableB", [_data_row("f2")]),
    )
    # Append another boundary row with an already-seen table name
    extra = pd.DataFrame([_boundary_row("tableA"), _data_row("f3")])
    df = pd.concat([df, extra]).reset_index(drop=True)
    with pytest.raises(ValueError, match="tableA"):
        splitup_metadata_sheet(df)


def test_splitup_drops_all_na_rows():
    df = _make_metadata_df(("tableA", [_data_row("f1")]))
    empty_row = pd.DataFrame(
        [{DictionaryColumns.FIELD_NAME: None, DictionaryColumns.DATA_TYPE: None}]
    )
    df = pd.concat([df, empty_row]).reset_index(drop=True)
    result = splitup_metadata_sheet(df)
    # The all-NaN row should be dropped, not appear as a new table
    assert set(result.keys()) == {"tableA"}

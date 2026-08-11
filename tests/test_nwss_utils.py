"""
Tests for odm_linkmlgen.nwss.nwss_utils: splitup_metadata_sheet, which splits a
flat NWSS metadata sheet into one DataFrame per table, and resolve_slot_enums,
which decides which enumeration each categorical field uses.
"""

import logging

import pandas as pd
import pytest

from odm_linkmlgen.nwss.nwss_utils import (
    SINGLE_TABLE_NAME,
    TABLE_NAME_COL,
    DictionaryColumns,
    SlotToEnumColumns,
    field_name_column,
    group_detailed_enums,
    parse_value_set_reference,
    resolve_slot_enums,
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


# --- field_name_column ---


def test_field_name_column_prefers_field_name():
    df = pd.DataFrame(
        columns=[DictionaryColumns.VARIABLE_NAME, DictionaryColumns.FIELD_NAME]
    )
    assert field_name_column(df) == DictionaryColumns.FIELD_NAME


def test_field_name_column_falls_back_to_variable_name():
    df = pd.DataFrame(columns=[DictionaryColumns.VARIABLE_NAME])
    assert field_name_column(df) == DictionaryColumns.VARIABLE_NAME


def test_field_name_column_missing_returns_none():
    assert field_name_column(pd.DataFrame(columns=["something else"])) is None


# --- parse_value_set_reference ---


def test_parse_value_set_reference_extracts_name():
    assert parse_value_set_reference("[See Value Sets: vs_yn]") == "vs_yn"


def test_parse_value_set_reference_without_colon_is_none():
    # Not a value set reference at all, so it must not be read as one
    assert parse_value_set_reference("[no reference here]") is None


def test_parse_value_set_reference_non_string_is_none():
    # A non-categorical field leaves the cell empty, which pandas reads as NaN
    assert parse_value_set_reference(float("nan")) is None
    assert parse_value_set_reference(None) is None


# --- resolve_slot_enums ---


def _category_row(field_name: str, value_set: str | None = None) -> dict:
    """A categorical Metadata row, optionally referencing an enumeration."""
    return {
        DictionaryColumns.FIELD_NAME: field_name,
        DictionaryColumns.DATA_TYPE: "category",
        DictionaryColumns.VALUE_SET: (
            f"[See Value Sets: {value_set}]" if value_set else None
        ),
    }


def _slot_to_enum_df(mapping: dict[str, str]) -> pd.DataFrame:
    """The Field -> Value Set Name mapping from the Value Sets sheet."""
    return pd.DataFrame(
        [
            {SlotToEnumColumns.SLOT: slot, SlotToEnumColumns.ENUM: enum}
            for slot, enum in mapping.items()
        ]
    )


def test_resolve_uses_metadata_value_set():
    metadata = pd.DataFrame([_category_row("sample_matrix", "vs_sample_matrix")])
    resolved = resolve_slot_enums(metadata)
    assert resolved["sample_matrix"].base == "vs_sample_matrix"
    assert resolved["sample_matrix"].name == "vs_sample_matrix"


def test_resolve_metadata_wins_over_value_sets_sheet():
    # The pretreatment defect: the two sheets name different enumerations. The
    # Metadata sheet is the authority, so the range and the generated enumeration
    # agree on vs_yn.
    metadata = pd.DataFrame([_category_row("pretreatment", "vs_yn")])
    slot_to_enum = _slot_to_enum_df({"pretreatment": "vs_yne"})
    resolved = resolve_slot_enums(metadata, slot_to_enum)
    assert resolved["pretreatment"].base == "vs_yn"


def test_resolve_conflict_is_logged(caplog):
    metadata = pd.DataFrame([_category_row("pretreatment", "vs_yn")])
    slot_to_enum = _slot_to_enum_df({"pretreatment": "vs_yne"})
    with caplog.at_level(logging.ERROR):
        resolve_slot_enums(metadata, slot_to_enum)
    assert "pretreatment" in caplog.text
    assert "vs_yn" in caplog.text and "vs_yne" in caplog.text


def test_resolve_conflict_not_logged_when_suppressed(caplog):
    metadata = pd.DataFrame([_category_row("pretreatment", "vs_yn")])
    slot_to_enum = _slot_to_enum_df({"pretreatment": "vs_yne"})
    with caplog.at_level(logging.ERROR):
        resolve_slot_enums(metadata, slot_to_enum, log_problems=False)
    assert caplog.text == ""


def test_resolve_falls_back_to_value_sets_sheet():
    # Fields absent from the Metadata sheet's Value Set column are common
    metadata = pd.DataFrame([_category_row("qc_ignore", None)])
    slot_to_enum = _slot_to_enum_df({"qc_ignore": "vs_yne"})
    resolved = resolve_slot_enums(metadata, slot_to_enum)
    assert resolved["qc_ignore"].base == "vs_yne"


def test_resolve_applies_detailed_name():
    metadata = pd.DataFrame([_category_row("pretreatment", "vs_yn")])
    resolved = resolve_slot_enums(metadata, detailed_enum_names=["vs_yn"])
    assert resolved["pretreatment"].base == "vs_yn"
    assert resolved["pretreatment"].name == "vs_yn[pretreatment]"


def test_resolve_leaves_undetailed_enum_alone():
    metadata = pd.DataFrame([_category_row("sample_matrix", "vs_sample_matrix")])
    resolved = resolve_slot_enums(metadata, detailed_enum_names=["vs_yn"])
    assert resolved["sample_matrix"].name == "vs_sample_matrix"


def test_resolve_skips_non_categorical_rows():
    metadata = pd.DataFrame(
        [
            _category_row("sample_matrix", "vs_sample_matrix"),
            {
                DictionaryColumns.FIELD_NAME: "sample_id",
                DictionaryColumns.DATA_TYPE: "string",
                DictionaryColumns.VALUE_SET: None,
            },
        ]
    )
    assert set(resolve_slot_enums(metadata)) == {"sample_matrix"}


def test_resolve_omits_categorical_slot_with_no_enum(caplog):
    metadata = pd.DataFrame([_category_row("pcr_target_units", None)])
    with caplog.at_level(logging.ERROR):
        resolved = resolve_slot_enums(metadata)
    assert "pcr_target_units" not in resolved
    assert "No enumeration" in caplog.text


def test_resolve_handles_variable_name_column():
    metadata = pd.DataFrame(
        [
            {
                DictionaryColumns.VARIABLE_NAME: "sample_matrix",
                DictionaryColumns.DATA_TYPE: "category",
                DictionaryColumns.VALUE_SET: "[See Value Sets: vs_sample_matrix]",
            }
        ]
    )
    assert resolve_slot_enums(metadata)["sample_matrix"].base == "vs_sample_matrix"


def test_resolve_without_value_set_column():
    metadata = pd.DataFrame(
        [
            {
                DictionaryColumns.FIELD_NAME: "qc_ignore",
                DictionaryColumns.DATA_TYPE: "category",
            }
        ]
    )
    slot_to_enum = _slot_to_enum_df({"qc_ignore": "vs_yne"})
    assert resolve_slot_enums(metadata, slot_to_enum)["qc_ignore"].base == "vs_yne"


# --- group_detailed_enums ---


def test_group_detailed_enums_groups_by_base():
    metadata = pd.DataFrame(
        [
            _category_row("pretreatment", "vs_yn"),
            _category_row("stormwater_input", "vs_yne"),
            _category_row("ext_blank", "vs_yne"),
            _category_row("sample_matrix", "vs_sample_matrix"),
        ]
    )
    resolved = resolve_slot_enums(metadata, detailed_enum_names=["vs_yn", "vs_yne"])
    grouped = group_detailed_enums(resolved)
    assert grouped["vs_yn"] == ["vs_yn[pretreatment]"]
    assert grouped["vs_yne"] == ["vs_yne[stormwater_input]", "vs_yne[ext_blank]"]
    # Enumerations that were not given a detailed name are not copied per slot
    assert "vs_sample_matrix" not in grouped


def test_group_detailed_enums_empty_when_nothing_detailed():
    metadata = pd.DataFrame([_category_row("sample_matrix", "vs_sample_matrix")])
    assert group_detailed_enums(resolve_slot_enums(metadata)) == {}

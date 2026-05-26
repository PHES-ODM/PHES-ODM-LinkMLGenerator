import pandas as pd

from odm_linkmlgen.odm.odm_utils import (
    odm_get_available_class_names,
    odm_get_enum_name_from_part_id,
    odm_keep_active_rows,
    odm_get_header_rows,
)


# --- odm_get_available_class_names ---


def test_get_class_names_from_list():
    headers = ["partID", "samplesOrder", "measuresOrder", "status"]
    assert odm_get_available_class_names(headers) == ["samples", "measures"]


def test_get_class_names_from_dataframe():
    df = pd.DataFrame(columns=["partID", "samplesOrder", "measuresOrder"])
    assert odm_get_available_class_names(df) == ["samples", "measures"]


def test_get_class_names_excludes_exact_tag():
    # A column whose name IS "Order" (no prefix) should be excluded
    assert odm_get_available_class_names(["Order"]) == []


def test_get_class_names_empty():
    assert odm_get_available_class_names([]) == []


# --- odm_get_enum_name_from_part_id ---


def test_enum_name_default_adds_s():
    assert odm_get_enum_name_from_part_id("sample") == "samples"


def test_enum_name_exception_class():
    assert odm_get_enum_name_from_part_id("class") == "classes"


def test_enum_name_exception_measure():
    assert odm_get_enum_name_from_part_id("measure") == "measurements"


def test_enum_name_not_in_recognized_returns_string():
    assert (
        odm_get_enum_name_from_part_id("sample", recognized_enums=["other"]) == "string"
    )


def test_enum_name_in_recognized_returns_name():
    assert (
        odm_get_enum_name_from_part_id("sample", recognized_enums=["samples"])
        == "samples"
    )


# --- odm_keep_active_rows ---


def test_keep_active_rows_filters_correctly():
    df = pd.DataFrame({"status": ["active", "inactive", "active"], "val": [1, 2, 3]})
    result = odm_keep_active_rows(df)
    assert result["val"].tolist() == [1, 3]


def test_keep_active_rows_strips_whitespace():
    df = pd.DataFrame({"status": [" active ", "inactive"], "val": [1, 2]})
    result = odm_keep_active_rows(df)
    assert result["val"].tolist() == [1]


def test_keep_active_rows_returns_copy():
    df = pd.DataFrame({"status": ["active"], "val": [1]})
    result = odm_keep_active_rows(df)
    result["val"] = 99
    assert df["val"].iloc[0] == 1


# --- odm_get_header_rows ---


def test_get_header_rows_returns_pk_and_header():
    df = pd.DataFrame(
        {
            "partID": ["id1", "id2", "id3"],
            "samples": ["pK", "header", "input"],
        }
    )
    result = odm_get_header_rows(df, "samples")
    assert set(result["partID"].tolist()) == {"id1", "id2"}


def test_get_header_rows_case_insensitive():
    df = pd.DataFrame(
        {
            "partID": ["id1", "id2"],
            "samples": ["PK", "HEADER"],
        }
    )
    result = odm_get_header_rows(df, "samples")
    assert len(result) == 2


def test_get_header_rows_multiple_tables():
    df = pd.DataFrame(
        {
            "partID": ["id1", "id2", "id3"],
            "samples": ["pK", None, None],
            "measures": [None, "header", None],
        }
    )
    result = odm_get_header_rows(df, ["samples", "measures"])
    assert set(result["partID"].tolist()) == {"id1", "id2"}


def test_get_header_rows_custom_header_tags():
    df = pd.DataFrame(
        {
            "partID": ["id1", "id2"],
            "samples": ["pK", "fK"],
        }
    )
    result = odm_get_header_rows(df, "samples", header_tags=["pK"])
    assert result["partID"].tolist() == ["id1"]

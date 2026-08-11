"""
Tests for odm_linkmlgen.utils.schema_utils: get_ranges_of_slot_defn, which reads a
slot's range(s) from either a "range" or an "any_of" definition, and
find_undefined_ranges, which finds slots whose range the schema never defines.
"""

import yaml
from linkml_runtime import SchemaView

from odm_linkmlgen.utils.schema_utils import (
    find_undefined_ranges,
    get_ranges_of_slot_defn,
)


def test_range_only():
    assert get_ranges_of_slot_defn({"range": "string"}) == ["string"]


def test_any_of_only():
    slot = {"range": None, "any_of": [{"range": "typeA"}, {"range": "typeB"}]}
    assert get_ranges_of_slot_defn(slot) == ["typeA", "typeB"]


def test_neither_range_nor_any_of_returns_empty():
    assert get_ranges_of_slot_defn({"range": None}) == []


def test_any_of_overrides_range():
    slot = {"range": "string", "any_of": [{"range": "typeA"}]}
    assert get_ranges_of_slot_defn(slot) == ["typeA"]


def test_multiple_slot_defns():
    slots = [{"range": "typeA"}, {"range": "typeB"}]
    assert get_ranges_of_slot_defn(slots) == ["typeA", "typeB"]


def test_deduplicates_across_multiple_defns():
    slots = [{"range": "typeA"}, {"range": "typeA"}]
    assert get_ranges_of_slot_defn(slots) == ["typeA"]


def test_any_of_entry_without_range_skipped():
    slot = {"range": None, "any_of": [{"pattern": ".*"}, {"range": "typeA"}]}
    assert get_ranges_of_slot_defn(slot) == ["typeA"]


def test_empty_any_of_falls_back_to_range():
    slot = {"range": "string", "any_of": [{"pattern": ".*"}]}
    assert get_ranges_of_slot_defn(slot) == ["string"]


def test_single_dict_wrapped_automatically():
    result = get_ranges_of_slot_defn({"range": "integer"})
    assert result == ["integer"]


def test_list_range_returns_each_range():
    # A slot with several ranges holds them as a list, see
    # schemasheets_utils.fix_schemasheets_generated_schema
    slot = {"range": ["typeA", "typeB"]}
    assert get_ranges_of_slot_defn(slot) == ["typeA", "typeB"]


# --- find_undefined_ranges ---


def _schema_view(classes: dict, enums: dict | None = None) -> SchemaView:
    """Build a SchemaView from a minimal LinkML schema."""
    schema = {
        "name": "test",
        "id": "https://example.org/test",
        "imports": ["linkml:types"],
        "prefixes": {"linkml": "https://w3id.org/linkml/"},
        "default_range": "string",
        "classes": classes,
    }
    if enums:
        schema["enums"] = enums
    return SchemaView(yaml.dump(schema))


def test_find_undefined_ranges_none_when_all_resolve():
    view = _schema_view(
        classes={
            "Sample": {
                "attributes": {
                    "sample_id": {"range": "string"},
                    "matrix": {"range": "vs_sample_matrix"},
                }
            }
        },
        enums={"vs_sample_matrix": {"permissible_values": {"raw": {}}}},
    )
    assert find_undefined_ranges(view) == {}


def test_find_undefined_ranges_reports_missing_enum():
    # The pretreatment defect: the range names an enumeration that was never
    # generated. LinkML loads this without complaint, which is the whole problem.
    view = _schema_view(
        classes={
            "nwss": {"attributes": {"pretreatment": {"range": "vs_yne[pretreatment]"}}}
        },
        enums={"vs_yn[pretreatment]": {"permissible_values": {"yes": {}}}},
    )
    assert find_undefined_ranges(view) == {
        "nwss.pretreatment": ["vs_yne[pretreatment]"]
    }


def test_find_undefined_ranges_accepts_a_class_as_a_range():
    view = _schema_view(
        classes={
            "Container": {"attributes": {"samples": {"range": "Sample"}}},
            "Sample": {"attributes": {"sample_id": {"range": "string"}}},
        }
    )
    assert find_undefined_ranges(view) == {}


def test_find_undefined_ranges_accepts_imported_types():
    view = _schema_view(
        classes={"Sample": {"attributes": {"collected": {"range": "date"}}}}
    )
    assert find_undefined_ranges(view) == {}

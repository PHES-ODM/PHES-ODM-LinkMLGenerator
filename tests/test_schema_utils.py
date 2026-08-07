"""
Tests for odm_linkmlgen.utils.schema_utils.get_ranges_of_slot_defn, which reads a
slot's range(s) from either a "range" or an "any_of" definition.
"""

from odm_linkmlgen.utils.schema_utils import get_ranges_of_slot_defn


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

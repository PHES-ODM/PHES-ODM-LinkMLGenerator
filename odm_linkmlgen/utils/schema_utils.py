"""
Utility functions for LinkML schemas.
"""

from typing import Dict, List, Union
from dataclasses import asdict
from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SlotDefinition

def get_slot_definition(
    cls: str, slot: str, schema: SchemaView, exception_on_error: bool = True
) -> Dict:
    """Get the full definition for the slot. This includes fields that are attributes of the class.
    If a slot is modified with a slot_usage, then we also update the returned dictionary with the
    slot usage information.

    Args:
        cls (str): The class that contains the slot.
        slot (str): The slot name to get the definition for.
        schema (SchemaView): The Schema the class and slot belong to.
        exception_on_error (bool): If True then raise an exception if the slot does not exist. If False then
            return None if the slot does not exist.

    Returns:
        Dict: The dictionary with all information about the slot (eg. the name, range, pattern, etc).
            If the slot is not a member of the class then None is returned.
    """
    if exception_on_error:
        return asdict(schema.induced_slot(slot, cls))
    else:
        try:
            return asdict(schema.induced_slot(slot, cls))
        except Exception:
            return None

def get_ranges_of_slot(
    class_name: str,
    slot_name: Union[str, List[str]],
    schema: SchemaView,
    exception_on_error: bool = True,
) -> List[str]:
    """Get the range(s) (if any) of the slot(s) in the specified class.

    Args:
        cls (str): The class that the slot belongs to.
        slot (Union[str, List[str]]): The slot(s) to get the range(s) for.
        schema (SchemaView): The Schema to retrieve the slot info from.
        exception_on_error (bool): If True then raise an exception if the a slot does not exist. If False then
            an empty range is retrieved for slots that do not exist.

    Returns:
        List[str]: A list of range(s) for the specified slots, if at least one range exists. If
            no range is found (eg. the class or slot are invalid) then an empty list is returned.
    """
    if isinstance(slot_name, str):
        slot_name = [slot_name]
    ranges = []
    for cur_slot in slot_name:
        # slot_defn = schema.induced_slot(cur_slot, class_name)
        slot_defn = get_slot_definition(
            class_name, cur_slot, schema, exception_on_error=exception_on_error
        )
        if slot_defn:
            cur_ranges = get_ranges_of_slot_defn(slot_defn)
            if cur_ranges:
                ranges.extend(cur_ranges)

    # Remove duplicates (but retain order)
    ranges = list(dict.fromkeys(ranges))
    return ranges


def get_ranges_of_slot_defn(
    slot_defn: Union[Dict, SlotDefinition, List[SlotDefinition]],
) -> List[str]:
    """Get the range(s) (if any) of the slot definition(s).

    Args:
        slot_defn (Union[Dict, SlotDefinition, List[SlotDefinition]]): The SlotDefinition(s) to get the ranges of.

    Returns:
        List[str]: A list of range(s) for the specified slot(s), if at least one range exists. If
            no range is found then an empty list is returned.
    """
    if isinstance(slot_defn, (SlotDefinition, Dict)):
        slot_defn = [slot_defn]
    ranges = []
    for cur_defn in slot_defn:
        if not isinstance(cur_defn, dict):
            cur_defn = asdict(cur_defn)
        # Try getting the range
        range_defn = cur_defn.get("range", None)
        if range_defn is not None:
            # range_defn is of type linkml_runtime.linkml_model.meta.ElementName
            # We need to convert it to either type str or type List[str]
            cur_ranges = [str(range_defn)]

        # Try getting any_of
        any_of_defn = cur_defn.get("any_of", None)
        if any_of_defn is not None:
            any_of_ranges = []
            for cur_defn in any_of_defn:
                cur_range = cur_defn.get("range", None)
                if cur_range:
                    any_of_ranges.append(str(cur_range))
            if len(any_of_ranges):
                cur_ranges = any_of_ranges

        ranges.extend(cur_ranges)

    # Remove duplicates (but retain order)
    ranges = list(dict.fromkeys(ranges))
    return ranges
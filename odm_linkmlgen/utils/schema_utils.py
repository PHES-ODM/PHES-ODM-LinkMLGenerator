"""
Utility functions for LinkML schemas.
"""

from dataclasses import asdict

from linkml_runtime import SchemaView
from linkml_runtime.linkml_model import SlotDefinition
from linkml_runtime.linkml_model.meta import SchemaDefinition


def get_slot_definition(
    cls: str, slot: str, schema: SchemaView, exception_on_error: bool = True
) -> dict | None:
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
        dict | None: The dictionary with all information about the slot (eg. the name, range, pattern,
            etc). If the slot is not a member of the class then None is returned.
    """
    if exception_on_error:
        return asdict(schema.induced_slot(slot, cls))
    else:
        try:
            return asdict(schema.induced_slot(slot, cls))
        except ValueError:
            # SchemaView raises a ValueError if the class or slot does not exist
            return None


def get_ranges_of_slot(
    class_name: str,
    slot_name: str | list[str],
    schema: SchemaView,
    exception_on_error: bool = True,
) -> list[str]:
    """Get the range(s) (if any) of the slot(s) in the specified class.

    Args:
        class_name (str): The class that the slot belongs to.
        slot_name (str | list[str]): The slot(s) to get the range(s) for.
        schema (SchemaView): The Schema to retrieve the slot info from.
        exception_on_error (bool): If True then raise an exception if the a slot does not exist. If False then
            an empty range is retrieved for slots that do not exist.

    Returns:
        list[str]: A list of range(s) for the specified slots, if at least one range exists. If
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
    slot_defn: dict | SlotDefinition | list[SlotDefinition],
) -> list[str]:
    """Get the range(s) (if any) of the slot definition(s).

    Args:
        slot_defn (dict | SlotDefinition | list[SlotDefinition]): The SlotDefinition(s) to get the ranges of.

    Returns:
        list[str]: A list of range(s) for the specified slot(s), if at least one range exists. If
            no range is found then an empty list is returned.
    """
    if isinstance(slot_defn, (SlotDefinition, dict)):
        slot_defn = [slot_defn]
    ranges = []
    for cur_defn in slot_defn:
        cur_ranges = []

        if not isinstance(cur_defn, dict):
            cur_defn = asdict(cur_defn)
        # Try getting the range
        range_defn = cur_defn.get("range", None)
        if range_defn is not None:
            # range_defn is of type linkml_runtime.linkml_model.meta.ElementName
            # We need to convert it to either type str or type list[str]. A slot with
            # several ranges holds them as a list (see
            # schemasheets_utils.fix_schemasheets_generated_schema).
            if isinstance(range_defn, (list, tuple)):
                cur_ranges = [str(r) for r in range_defn]
            else:
                cur_ranges = [str(range_defn)]

        # Try getting any_of. This overrides what we retrieved from "range".
        # For example, sometimes we might have "range: Any" and "any_of: ...",
        # which in LinkML means to use the "any_of" field, but having "range: Any"
        # is not required.
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


def find_undefined_ranges(
    schema: SchemaDefinition | SchemaView,
) -> dict[str, list[str]]:
    """Find every slot whose range names something the schema does not define.

    A generated schema can be well-formed YAML, and can load, while still being unusable:
    LinkML does not resolve ranges when a schema is loaded, so a slot whose range names an
    enumeration that was never generated passes unnoticed until whatever consumes the
    schema tries to use it. The generators log and skip a bad data dictionary row rather
    than raising, so this is the check that turns a skipped row into a reported problem.

    Args:
        schema (SchemaDefinition | SchemaView): The schema to check.

    Returns:
        dict[str, list[str]]: The undefined ranges of each offending slot, keyed by
            "{class_name}.{slot_name}". Empty if every range resolves.
    """
    view = schema if isinstance(schema, SchemaView) else SchemaView(schema)

    # Everything a range is allowed to name. all_types() includes the imported
    # linkml:types, so string, integer, date and the rest are covered as long as the
    # import resolved.
    defined = set(view.all_classes()) | set(view.all_enums()) | set(view.all_types())

    undefined = {}
    for class_name in view.all_classes():
        for slot_defn in view.class_induced_slots(class_name):
            missing = [
                range_name
                for range_name in get_ranges_of_slot_defn(slot_defn)
                if range_name not in defined
            ]
            if missing:
                undefined[f"{class_name}.{slot_defn.name}"] = missing

    return undefined

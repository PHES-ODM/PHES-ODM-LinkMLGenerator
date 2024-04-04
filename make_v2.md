# Generating the ODM v2 LinkML Schema

The ODM v2 Data Dictionary is much more complicated than the v1 dictionary. As such generating the ODM v2 LinkML schema is more complex. To make things simple, we have included a single script that will do all the processing and generation of the LinkML schema in one easy step. For details on running the [src/make_v2.py](src/make_v2.py) script see the main [README](README.md). Importantly, you must obtain the ODM v2 data dictionary Excel file, see the [README](README.md) for details.

A detailed description of the steps that the [src/make_v2.py](src/make_v2.py) script performs to generate the schema are described below.

## utils.general_utils.clear_dirs

The output directories are first cleaned by removing any old CSV, TSV, and YAML files. This is to ensure no artefacts are left over from previous runs.

## utils.general_utils.extract_sheets

The original data dictionary is an Excel file. The function extract_sheets extracts the required Excel sheets from the data dictionary as CSV files and saves them to disk (by default at `gen/odm_v2/dictionary`). The sheets "parts" and "sets" are extracted.

## odm_v2.make_v2_ss_classes.extract_all_classes

The parts sheet contains (among others) all classes (which are equivalent to tables) for the data model including all slots (which are equivalent to columns or fields) for those classes. Slots and their information are found in rows of the parts sheet that are identified as either a "pK" (primary key), "fK" (foreign key), or "header" for the class. These tags (pK, fK, and header) are found in a column of the parts sheet that has the same name as the class. For example, all slots for the "measures" table will have one of these tags in the column named "measures" in the parts sheet. The name of the slot itself is found in the "partID" column.

The `extract_all_classes` function extracts one class at a time, outputing the results to `gen/odm_v2/schemasheets/class_{class_name}.tsv`.

## odm_v2.make_v2_ss_container.extract_container_class

The top-level LinkML class is the container class. It contains all the tables and is marked as the tree root. Each of the container's slots point to a table in ODM v2 (eg. the measures and protocols tables). These slots
have a range equal to each of the table classes (ie. the slots are rows of each class, forming a table).

The `extract_container_class` function extracts the container class and saves the result to `gen/odm_v2/schemasheets/container.tsv`.

## odm_v2.make_v2_ss_enums_from_sets.extract_sets_enums

The data dictionary includes a sheet named "sets" that contains a list of many (but not all) enumerations. `extract_sets_enums` will extract the enumerations in the "sets" sheet and save them to `gen/odm_v2/schemasheets/enums_sets.tsv`.

## odm_v2.make_v2_ss_enums_from_parts.extract_parts_enums

While many of the enumerations are found in the "sets" sheet, there are still many that are found within the "parts" sheet. The "parts" sheet is more complicated to process. Within the "dataType" column, if a row is identified as "categorical" then the variable for that row can take on a value from an enumeration. If the "mmaSet" column is set for that row, then it will list the enumeration as found in the "sets" sheet. If "mmaSet" is not set, then the enumeration is not defined in the "sets" sheet and instead needs to be extracted from the "parts" sheet by finding all rows that correspond to the enumeration. Rows with the enumeration name found in the "partType" column are permissible values for the enumeration. `extract_parts_enums` will extract all of these enumerations with their permissible values and save them in `gen/odm_v2/schemasheets/enums_parts.tsv`.

## odm_v2.make_v2_ss_prefixes.make_prefixes

This function will make the Schemasheet `gen/odm_v2/schemasheets/prefixes.tsv` that defines the prefixes used as part of CURIEs by the data dictionary. This includes the "odmv2" prefix.

## odm_v2.make_v2_ss_schema.make_schema

This function will make the Schemasheet `gen/odm_v2/schemasheets/schema.tsv` that contains metadata for the top-level schema. This includes the schema name, ID, description, and default prefix.

## utils.general_utils.make_linkml_schema

This function will generate the final LinkML schema for ODM v2. It does this by executing Schemasheets on all the previously generated TSV files. The final schema will be placed at `gen/odm_v2/linkml/odm_v2.yaml`.

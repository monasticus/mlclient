from mlclient.xquery import cts


def run():
    return cts.field_value_ranges(
        "field-names", bounds=["bounds", 123, 2.5, True],
    ).compile()

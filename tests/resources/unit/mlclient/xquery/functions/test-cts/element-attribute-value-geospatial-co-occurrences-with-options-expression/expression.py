from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_value_geospatial_co_occurrences(
        "item", "id", "item", options=fn.string(cts.search().pos(1)),
    ).compile()

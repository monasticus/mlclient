from mlclient.xquery import cts, fn


def run():
    return cts.element_value_geospatial_co_occurrences(
        "item", "item", coord_child_name_1=fn.string(cts.search().pos(1)),
    ).compile()

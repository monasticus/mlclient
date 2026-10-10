from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_element_child_reference(
        "item",
        "child",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()

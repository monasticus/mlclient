from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_element_child_reference(
        "item", fn.string(cts.search().pos(1)),
    ).compile()

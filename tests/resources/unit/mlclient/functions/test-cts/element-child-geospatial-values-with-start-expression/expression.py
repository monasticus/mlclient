from mlclient.functions.xqy import cts


def run():
    return cts.element_child_geospatial_values(
        "item", "child-names", start=cts.search().index(1),
    ).compile()

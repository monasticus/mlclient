from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_json_property_child_reference(
        fn.string(cts.search().pos(1)), "child",
    ).compile()

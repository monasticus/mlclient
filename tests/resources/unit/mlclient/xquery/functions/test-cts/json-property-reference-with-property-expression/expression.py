from mlclient.xquery import cts, fn


def run():
    return cts.json_property_reference(fn.string(cts.search().pos(1))).compile()

from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_value_ranges(
        "item", bounds=fn.count(cts.search().pos(1)),
    ).compile()

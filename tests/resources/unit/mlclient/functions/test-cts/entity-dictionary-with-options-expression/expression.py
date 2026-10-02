from mlclient.functions.xqy import cts, fn


def run():
    return cts.entity_dictionary(
        cts.search().pos(1), options=fn.string(cts.search().pos(1)),
    ).compile()

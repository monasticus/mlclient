from mlclient.functions.xqy import cts, fn


def run():
    return cts.entity_dictionary(
        cts.search().index(1), options=fn.string(cts.search().index(1)),
    ).compile()

from mlclient.functions.xqy import cts, fn


def run():
    return cts.entity_dictionary_get(fn.string(cts.search().pos(1))).compile()

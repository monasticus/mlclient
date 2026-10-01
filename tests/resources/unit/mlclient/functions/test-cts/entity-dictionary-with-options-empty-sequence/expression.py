from mlclient.functions.xqy import cts


def run():
    return cts.entity_dictionary(cts.search().index(1), options=None).compile()

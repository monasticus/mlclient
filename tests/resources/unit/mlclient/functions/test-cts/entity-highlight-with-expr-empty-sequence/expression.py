from mlclient.functions.xqy import cts


def run():
    return cts.entity_highlight(cts.search().index(1), None).compile()

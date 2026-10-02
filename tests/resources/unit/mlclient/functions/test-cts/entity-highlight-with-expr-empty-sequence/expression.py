from mlclient.functions.xqy import cts


def run():
    return cts.entity_highlight(cts.search().pos(1), None).compile()

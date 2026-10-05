from mlclient.functions.xqy import cts


def run():
    return cts.highlight(cts.search().pos(1), "needle", None).compile()

from mlclient.functions.xqy import cts


def run():
    return cts.highlight(cts.search().index(1), "needle", None).compile()

from mlclient.functions.xqy import cts


def run():
    return cts.contains(
        [cts.search().index(1), cts.search().index(2)], "needle",
    ).compile()

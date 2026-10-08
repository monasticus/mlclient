from mlclient.xquery import cts


def run():
    return cts.contains(
        [cts.search().pos(1), cts.search().pos(2)], "needle",
    ).compile()

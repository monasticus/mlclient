from mlclient.xquery import cts


def run():
    return cts.lsqt_query("temporal", weight=2.5).compile()

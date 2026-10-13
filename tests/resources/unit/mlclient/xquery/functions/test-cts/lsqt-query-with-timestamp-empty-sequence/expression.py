from mlclient.xquery import cts


def run():
    return cts.lsqt_query("temporal", timestamp=None).compile()

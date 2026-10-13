from mlclient.xquery import cts


def run():
    return cts.lsqt_query("temporal", options=["checked"]).compile()

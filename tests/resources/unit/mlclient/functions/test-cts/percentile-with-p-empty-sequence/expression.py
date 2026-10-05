from mlclient.functions.xqy import cts


def run():
    return cts.percentile(2.5, None).compile()

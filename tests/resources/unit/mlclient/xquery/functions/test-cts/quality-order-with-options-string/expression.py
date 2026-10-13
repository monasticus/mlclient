from mlclient.xquery import cts


def run():
    return cts.quality_order(options="checked").compile()

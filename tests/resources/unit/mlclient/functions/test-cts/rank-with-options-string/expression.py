from mlclient.functions.xqy import cts


def run():
    return cts.rank("arg", "value", options="checked").compile()

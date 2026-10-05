from mlclient.functions.xqy import cts


def run():
    return cts.word_match("prod*", options="checked").compile()

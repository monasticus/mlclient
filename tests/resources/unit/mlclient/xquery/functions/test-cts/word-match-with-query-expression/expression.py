from mlclient.xquery import cts


def run():
    return cts.word_match("prod*", query=cts.collection_query("products")).compile()

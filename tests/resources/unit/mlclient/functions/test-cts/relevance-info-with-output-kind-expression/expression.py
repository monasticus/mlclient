from mlclient.functions.xqy import cts, fn


def run():
    return cts.relevance_info(output_kind=fn.string(cts.search().index(1))).compile()

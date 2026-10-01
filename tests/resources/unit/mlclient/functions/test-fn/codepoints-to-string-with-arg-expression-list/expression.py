from mlclient.functions.xqy import cts, fn


def run():
    return fn.codepoints_to_string(
        [cts.search().index(1), cts.search().index(2)],
    ).compile()

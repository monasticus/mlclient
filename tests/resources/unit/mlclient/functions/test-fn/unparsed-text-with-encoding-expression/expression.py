from mlclient.functions.xqy import cts, fn


def run():
    return fn.unparsed_text(
        "document.txt", encoding=fn.string(cts.search().pos(1)),
    ).compile()

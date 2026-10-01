from mlclient.functions.xqy import cts, fn


def run():
    return fn.escape_html_uri(fn.string(cts.search().index(1))).compile()

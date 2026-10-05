from mlclient.functions.xqy import cts, fn


def run():
    return fn.format_number(fn.count(cts.search().pos(1)), "#,##0.00").compile()

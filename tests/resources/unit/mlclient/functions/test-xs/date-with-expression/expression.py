from mlclient.functions.xqy import fn, xs


def run():
    return xs.date(fn.current_date()).compile()

from mlclient.xquery import fn, xs


def run():
    return xs.date(fn.current_date()).compile()

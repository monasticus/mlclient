from mlclient.functions.xqy import fn, xs


def run():
    return xs.date_time(fn.current_date_time()).compile()

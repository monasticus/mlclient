from mlclient.xquery import fn


def run():
    return fn.timezone_from_date(fn.current_date()).compile()

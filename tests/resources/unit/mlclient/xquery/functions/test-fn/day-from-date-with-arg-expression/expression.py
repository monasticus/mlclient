from mlclient.xquery import fn


def run():
    return fn.day_from_date(fn.current_date()).compile()

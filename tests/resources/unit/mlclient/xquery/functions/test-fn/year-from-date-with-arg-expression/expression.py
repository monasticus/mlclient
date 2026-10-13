from mlclient.xquery import fn


def run():
    return fn.year_from_date(fn.current_date()).compile()

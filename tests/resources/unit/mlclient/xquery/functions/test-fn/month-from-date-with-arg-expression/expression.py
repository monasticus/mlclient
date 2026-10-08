from mlclient.xquery import fn


def run():
    return fn.month_from_date(fn.current_date()).compile()

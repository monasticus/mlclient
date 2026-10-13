from mlclient.xquery import fn


def run():
    return fn.month_from_date_time(fn.current_date_time()).compile()

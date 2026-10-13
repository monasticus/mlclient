from mlclient.xquery import fn


def run():
    return fn.hours_from_date_time(fn.current_date_time()).compile()

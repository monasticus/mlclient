from mlclient.functions.xqy import fn


def run():
    return fn.seconds_from_date_time(fn.current_date_time()).compile()

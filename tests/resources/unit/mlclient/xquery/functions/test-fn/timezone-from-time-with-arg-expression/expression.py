from mlclient.xquery import fn


def run():
    return fn.timezone_from_time(fn.current_time()).compile()

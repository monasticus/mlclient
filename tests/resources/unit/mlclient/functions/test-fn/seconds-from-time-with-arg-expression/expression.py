from mlclient.functions.xqy import fn


def run():
    return fn.seconds_from_time(fn.current_time()).compile()

from mlclient.xquery import fn


def run():
    return fn.minutes_from_duration("arg").compile()

from datetime import time
from mlclient.xquery import fn


def run():
    return fn.timezone_from_time(time(3, 4, 5)).compile()

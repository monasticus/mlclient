from datetime import time
from mlclient.functions.xqy import fn


def run():
    return fn.hours_from_time(time(3, 4, 5)).compile()

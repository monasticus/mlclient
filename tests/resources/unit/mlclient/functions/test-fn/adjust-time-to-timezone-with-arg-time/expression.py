from datetime import time
from mlclient.functions.xqy import fn


def run():
    return fn.adjust_time_to_timezone(time(3, 4, 5)).compile()

from datetime import time
from mlclient.xquery import fn


def run():
    return fn.adjust_time_to_timezone(time(3, 4, 5), timezone=None).compile()

from datetime import time
from mlclient.functions.xqy import fn


def run():
    return fn.date_time(object(), time(3, 4, 5))

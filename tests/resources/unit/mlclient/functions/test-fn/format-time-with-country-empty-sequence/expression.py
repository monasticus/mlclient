from datetime import time
from mlclient.functions.xqy import fn


def run():
    return fn.format_time(time(3, 4, 5), "[H01]:[m01]:[s01]", country=None).compile()

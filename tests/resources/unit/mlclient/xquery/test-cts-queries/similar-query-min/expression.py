from xml.etree.ElementTree import fromstring
from mlclient.xquery import cts


def run():
    return cts.similar_query(fromstring("<report>blue</report>"))

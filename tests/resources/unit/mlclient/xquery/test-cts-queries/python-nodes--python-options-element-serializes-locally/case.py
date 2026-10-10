from xml.etree.ElementTree import fromstring
from mlclient.xquery import cts


def run():
    options = fromstring(
        '<options xmlns="cts:distinctive-terms"><max-terms>20</max-terms></options>',
    )
    assert cts.similar_query({"label": "blue"}, options=options).to_json() == {
        "similarQuery": {"nodes": [{"label": "blue"}], "options": {"maxTerms": 20}},
    }

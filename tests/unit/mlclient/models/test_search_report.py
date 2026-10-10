from mlclient.models import SearchReport


def test_report_fields():
    results = [{"uri": "/products/a.xml", "score": 10}]
    facets = {"price": {"facetValues": [{"name": "1.25", "count": 1}]}}
    metrics = {"total-time": "PT0.001S"}
    response = {"total": 1, "results": results, "facets": facets, "metrics": metrics}
    report = SearchReport(1, 1, 10, results, facets, metrics, "12345", response)

    assert report.total == 1
    assert report.start == 1
    assert report.page_length == 10
    assert report.results is results
    assert report.facets is facets
    assert report.metrics is metrics
    assert report.effective_timestamp == "12345"
    assert report.response is response

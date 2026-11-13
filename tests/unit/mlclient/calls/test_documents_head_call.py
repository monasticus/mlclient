from mlclient.calls import ApiCall, DocumentsHeadCall


def test_is_api_call():
    assert issubclass(DocumentsHeadCall, ApiCall)


def test_endpoint():
    assert DocumentsHeadCall(uri="/a.json").endpoint == "/v1/documents"


def test_method():
    assert DocumentsHeadCall(uri="/a.json").method == "HEAD"


def test_parameters():
    assert DocumentsHeadCall(uri="/a.json").params == {"uri": "/a.json"}


def test_headers():
    assert DocumentsHeadCall(uri="/a.json").headers == {}


def test_body():
    assert DocumentsHeadCall(uri="/a.json").body is None


def test_fully_parametrized_call():
    call = DocumentsHeadCall(uri="/a.json", database="Documents", txid="12345")

    assert call.method == "HEAD"
    assert call.endpoint == "/v1/documents"
    assert call.headers == {}
    assert call.params == {
        "uri": "/a.json",
        "database": "Documents",
        "txid": "12345",
    }
    assert call.body is None

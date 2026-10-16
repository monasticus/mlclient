from mlclient.calls import ApiCall, HostConfigDeleteCall


def test_is_api_call():
    assert issubclass(HostConfigDeleteCall, ApiCall)


def test_endpoint():
    assert HostConfigDeleteCall().endpoint == "/admin/v1/host-config"


def test_method():
    assert HostConfigDeleteCall().method == "DELETE"


def test_parameters():
    assert HostConfigDeleteCall().params == {}


def test_headers():
    assert HostConfigDeleteCall().headers == {}


def test_body():
    assert HostConfigDeleteCall().body is None


def test_fully_parametrized_call():
    call = HostConfigDeleteCall(remote_host="departing-host.example.com")
    assert call.method == "DELETE"
    assert call.endpoint == "/admin/v1/host-config"
    assert call.headers == {}
    assert call.params == {"remote-host": "departing-host.example.com"}
    assert call.body is None

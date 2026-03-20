from mlclient.calls import ApiCall


class ApiCallTestImpl(ApiCall):
    """An ApiCall implementation for testing purposes"""

    @property
    def endpoint(self):
        return "/impl-endpoint"


class ApiCallTestInvalidImpl(ApiCall):
    """An ApiCall invalid implementation for testing purposes"""


def test_issubclass_true():
    assert issubclass(ApiCallTestImpl, ApiCall)


def test_issubclass_false():
    assert not issubclass(ApiCallTestInvalidImpl, ApiCall)


# endpoint
def test_endpoint():
    assert ApiCallTestImpl().endpoint == "/impl-endpoint"


# method
def test_default_method():
    assert ApiCallTestImpl().method == "GET"


def test_custom_method():
    assert ApiCallTestImpl(method="POST").method == "POST"


# set_method
def test_set_method():
    call = ApiCallTestImpl()
    assert call.method == "GET"

    call.method = "POST"
    assert call.method == "POST"


# params
def test_default_params():
    assert ApiCallTestImpl().params == {}


def test_custom_params():
    call_with_custom_param = ApiCallTestImpl(
        params={"custom-param": "custom-value"},
    )
    assert call_with_custom_param.params == {"custom-param": "custom-value"}


def test_params_encapsulation():
    call = ApiCallTestImpl()
    params = call.params
    assert params == {}

    params["custom-param"] = "custom-value"
    assert params == {"custom-param": "custom-value"}

    assert call.params == {}


# set_params
def test_set_params():
    call = ApiCallTestImpl()
    params = call.params
    assert params == {}

    call.params = {
        "custom-param": "custom-value",
    }
    assert call.params == {
        "custom-param": "custom-value",
    }


def test_set_params_with_none_value():
    call = ApiCallTestImpl(params={"custom-param-1": "custom-value"})
    params = call.params
    assert params == {"custom-param-1": "custom-value"}

    call.params = None
    assert call.params == {}


def test_set_params_with_none_param():
    call = ApiCallTestImpl()
    params = call.params
    assert params == {}

    call.params = {
        "custom-param-1": "custom-value",
        "custom-param-2": None,
    }
    assert call.params == {
        "custom-param-1": "custom-value",
    }


# headers
def test_default_headers():
    assert ApiCallTestImpl().headers == {}


def test_custom_headers():
    call_with_custom_header = ApiCallTestImpl(
        headers={"custom-header": "custom-value"},
    )
    assert call_with_custom_header.headers == {"custom-header": "custom-value"}


def test_custom_headers_with_none_value():
    call_with_custom_header = ApiCallTestImpl(headers={"custom-header": None})
    assert call_with_custom_header.headers == {}


def test_headers_with_accept():
    call_with_accept = ApiCallTestImpl(accept="application/xml")
    assert call_with_accept.headers == {"Accept": "application/xml"}


def test_headers_with_content_type():
    call_with_content_type = ApiCallTestImpl(content_type="application/xml")
    assert call_with_content_type.headers == {"Content-Type": "application/xml"}


def test_mixed_headers():
    call_with_mixed_headers = ApiCallTestImpl(
        headers={"custom-header": "custom-value"},
        accept="application/xml",
        content_type="application/xml",
    )
    assert call_with_mixed_headers.headers == {
        "custom-header": "custom-value",
        "Accept": "application/xml",
        "Content-Type": "application/xml",
    }


def test_headers_when_accept_exists_and_is_provided():
    call_with_custom_header = ApiCallTestImpl(
        headers={"Accept": "application/xml"},
        accept="application/json",
    )
    assert call_with_custom_header.headers == {"Accept": "application/json"}


def test_headers_when_content_type_exists_and_is_provided():
    call_with_custom_header = ApiCallTestImpl(
        headers={"Content-Type": "application/xml"},
        content_type="application/json",
    )
    assert call_with_custom_header.headers == {"Content-Type": "application/json"}


def test_headers_encapsulation():
    call = ApiCallTestImpl()
    headers = call.headers
    assert headers == {}

    headers["custom-header"] = "custom-value"
    assert headers == {"custom-header": "custom-value"}

    assert call.headers == {}


# set_headers
def test_set_headers():
    call = ApiCallTestImpl()
    headers = call.headers
    assert headers == {}

    call.headers = {
        "custom-header": "custom-value",
    }
    assert call.headers == {
        "custom-header": "custom-value",
    }


def test_set_headers_with_none_value():
    call = ApiCallTestImpl(headers={"custom-header-1": "custom-value"})
    headers = call.headers
    assert headers == {"custom-header-1": "custom-value"}

    call.headers = None
    assert call.headers == {}


def test_set_headers_with_none_header():
    call = ApiCallTestImpl()
    headers = call.headers
    assert headers == {}

    call.headers = {
        "custom-header-1": "custom-value",
        "custom-header-2": None,
    }
    assert call.headers == {
        "custom-header-1": "custom-value",
    }


# body
def test_default_body():
    assert not ApiCallTestImpl().body


def test_custom_string_body():
    assert ApiCallTestImpl(body="").body == ""


def test_custom_json_body():
    assert ApiCallTestImpl(body={}).body == {}


def test_custom_bytes_body():
    assert ApiCallTestImpl(body=b"").body == b""


def test_string_body_encapsulation():
    call = ApiCallTestImpl(body="")
    body = call.body
    assert body == ""

    body = "custom-body"
    assert body == "custom-body"

    assert call.body == ""


def test_dict_body_encapsulation():
    call = ApiCallTestImpl(body={})
    body = call.body
    assert body == {}

    body["custom-key"] = "custom-value"
    assert body == {"custom-key": "custom-value"}

    assert call.body == {}


def test_bytes_body_encapsulation():
    call = ApiCallTestImpl(body=b"")
    body = call.body
    assert body == b""

    body = b"custom-body"
    assert body == b"custom-body"

    assert call.body == b""


# set_body
def test_set_body():
    call = ApiCallTestImpl()
    assert call.body is None

    call.body = "custom-body"
    assert call.body == "custom-body"


def test_set_body_when_exists():
    call = ApiCallTestImpl(body="custom-body-1")
    assert call.body == "custom-body-1"

    call.body = "custom-body-2"
    assert call.body == "custom-body-2"


# add_param
def test_add_param():
    call = ApiCallTestImpl()
    assert call.params == {}

    call.add_param("custom-param", "custom-value")
    assert call.params == {"custom-param": "custom-value"}


def test_add_param_when_exists():
    call = ApiCallTestImpl(params={"custom-param": "custom-value-1"})
    assert call.params == {"custom-param": "custom-value-1"}

    call.add_param("custom-param", "custom-value-2")
    assert call.params == {"custom-param": "custom-value-2"}


# add_header
def test_add_header():
    call = ApiCallTestImpl()
    assert call.headers == {}

    call.add_header("custom-header", "custom-value")
    assert call.headers == {"custom-header": "custom-value"}


def test_add_header_when_exists():
    call = ApiCallTestImpl(headers={"custom-header": "custom-value-1"})
    assert call.headers == {"custom-header": "custom-value-1"}

    call.add_header("custom-header", "custom-value-2")
    assert call.headers == {"custom-header": "custom-value-2"}

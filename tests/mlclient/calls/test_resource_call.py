from mlclient.calls import ResourceCall


class ResourceCallTestImpl(ResourceCall):
    """A ResourceCall implementation for testing purposes"""

    def endpoint(self):
        return "/impl-endpoint"


# ResourceCall.endpoint()
def test_endpoint():
    assert ResourceCallTestImpl().endpoint() == "/impl-endpoint"


# ResourceCall.method()
def test_default_method():
    assert ResourceCallTestImpl().method() == "GET"


def test_custom_method():
    assert ResourceCallTestImpl(method="POST").method() == "POST"


def test_method_encapsulation():
    call = ResourceCallTestImpl()
    method = call.method()
    assert method == "GET"

    method = "POST"
    assert method == "POST"

    assert call.method() == "GET"


# params()
def test_default_params():
    assert ResourceCallTestImpl().params() == {}


def test_custom_params():
    call_with_custom_param = ResourceCallTestImpl(
        params={"custom-param": "custom-value"})
    assert call_with_custom_param.params() == {"custom-param": "custom-value"}


def test_params_encapsulation():
    call = ResourceCallTestImpl()
    params = call.params()
    assert {} == params

    params["custom-param"] = "custom-value"
    assert {"custom-param": "custom-value"} == params

    assert call.params() == {}


# headers()
def test_default_headers():
    assert ResourceCallTestImpl().headers() == {}


def test_custom_headers():
    call_with_custom_header = ResourceCallTestImpl(
        headers={"custom-header": "custom-value"})
    assert call_with_custom_header.headers() == {"custom-header": "custom-value"}


def test_headers_with_accept():
    call_with_accept = ResourceCallTestImpl(
        accept="application/xml")
    assert call_with_accept.headers() == {"accept": "application/xml"}


def test_headers_with_content_type():
    call_with_content_type = ResourceCallTestImpl(
        content_type="application/xml")
    assert call_with_content_type.headers() == {"content-type": "application/xml"}


def test_mixed_headers():
    call_with_mixed_headers = ResourceCallTestImpl(
        headers={"custom-header": "custom-value"},
        accept="application/xml",
        content_type="application/xml")
    assert call_with_mixed_headers.headers() == {
        "custom-header": "custom-value",
        "accept": "application/xml",
        "content-type": "application/xml",
    }


def test_headers_when_accept_exists_and_is_provided():
    call_with_custom_header = ResourceCallTestImpl(
        headers={"accept": "application/xml"},
        accept="application/json")
    assert call_with_custom_header.headers() == {"accept": "application/json"}


def test_headers_when_content_type_exists_and_is_provided():
    call_with_custom_header = ResourceCallTestImpl(
        headers={"content-type": "application/xml"},
        content_type="application/json")
    assert call_with_custom_header.headers() == {"content-type": "application/json"}


def test_headers_encapsulation():
    call = ResourceCallTestImpl()
    headers = call.headers()
    assert {} == headers

    headers["custom-header"] = "custom-value"
    assert headers == {"custom-header": "custom-value"}

    assert call.headers() == {}


# body()
def test_default_body():
    assert not ResourceCallTestImpl().body()


def test_custom_string_body():
    assert ResourceCallTestImpl(body="").body() == ""


def test_custom_json_body():
    assert ResourceCallTestImpl(body={}).body() == {}


def test_string_body_encapsulation():
    call = ResourceCallTestImpl(body="")
    body = call.body()
    assert body == ""

    body = "custom-body"
    assert body == "custom-body"

    assert call.body() == ""


def test_dict_body_encapsulation():
    call = ResourceCallTestImpl(body={})
    body = call.body()
    assert body == {}

    body["custom-key"] = "custom-value"
    assert body == {"custom-key": "custom-value"}

    assert call.body() == {}


# add_param()
def test_add_param():
    call = ResourceCallTestImpl()
    assert call.params() == {}

    call.add_param("custom-param", "custom-value")
    assert call.params() == {"custom-param": "custom-value"}


def test_add_param_when_exists():
    call = ResourceCallTestImpl(
        params={"custom-param": "custom-value-1"})
    assert call.params() == {"custom-param": "custom-value-1"}

    call.add_param("custom-param", "custom-value-2")
    assert call.params() == {"custom-param": "custom-value-2"}


# add_header()
def test_add_header():
    call = ResourceCallTestImpl()
    assert call.headers() == {}

    call.add_header("custom-header", "custom-value")
    assert call.headers() == {"custom-header": "custom-value"}


def test_add_header_when_exists():
    call = ResourceCallTestImpl(
        headers={"custom-header": "custom-value-1"})
    assert call.headers() == {"custom-header": "custom-value-1"}

    call.add_header("custom-header", "custom-value-2")
    assert call.headers() == {"custom-header": "custom-value-2"}


# set_body()
def test_set_body():
    call = ResourceCallTestImpl()
    assert call.body() is None

    call.set_body("custom-body")
    assert call.body() == "custom-body"


def test_set_body_when_exists():
    call = ResourceCallTestImpl(body="custom-body-1")
    assert call.body() == "custom-body-1"

    call.set_body("custom-body-2")
    assert call.body() == "custom-body-2"

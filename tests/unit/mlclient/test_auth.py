from __future__ import annotations

import base64
import sys
import types

import httpx
import pytest

from mlclient.auth import (
    AuthConfig,
    KerberosAuth,
    OAuthBearerAuth,
    auth_method_name,
    build_auth,
)


def test_build_auth_digest():
    auth = build_auth("digest", "user", "pass")
    assert isinstance(auth, httpx.DigestAuth)


def test_build_auth_basic():
    auth = build_auth("basic", "user", "pass")
    assert isinstance(auth, httpx.BasicAuth)


def test_build_auth_digestbasic():
    auth = build_auth("digestbasic", "user", "pass")
    assert isinstance(auth, httpx.DigestAuth)


def test_build_auth_none():
    assert build_auth(None, "user", "pass") is None


def test_build_auth_passthrough():
    custom = httpx.BasicAuth("user", "pass")
    assert build_auth(custom, "ignored", "ignored") is custom


def test_build_auth_certificate_returns_none():
    auth = build_auth(AuthConfig(method="certificate"), "user", "pass")
    assert auth is None


def test_build_auth_oauth():
    auth = build_auth(AuthConfig(method="oauth", token="abc"), "user", "pass")
    assert isinstance(auth, OAuthBearerAuth)


def test_build_auth_unknown_shortcut():
    with pytest.raises(ValueError, match="Unknown auth shortcut"):
        build_auth("cloud", "user", "pass")


def test_build_auth_certificate_string_returns_none():
    auth = build_auth("certificate", "user", "pass")
    assert auth is None


def test_build_auth_kerberos_string_builds_auth(monkeypatch):
    monkeypatch.setitem(sys.modules, "spnego", _FakeSpnego())
    auth = build_auth("kerberos", "user", "pass")
    assert isinstance(auth, KerberosAuth)


def test_build_auth_kerberos_string_uses_default_spn(monkeypatch):
    spnego = _FakeSpnego()
    monkeypatch.setitem(sys.modules, "spnego", spnego)
    auth = build_auth("kerberos", "user", "pass")

    request = httpx.Request("GET", "http://ml.example.com:8000/")
    flow = auth.auth_flow(request)
    first = next(flow)
    challenge = httpx.Response(
        httpx.codes.UNAUTHORIZED,
        headers={"WWW-Authenticate": "Negotiate"},
        request=first,
    )
    flow.send(challenge)

    assert spnego.context.spn == "HTTP/ml.example.com"


def test_build_auth_unknown_config_method():
    with pytest.raises(ValueError, match="Unknown auth method"):
        build_auth(AuthConfig(method="saml"), "user", "pass")


def test_build_auth_wrong_type():
    with pytest.raises(TypeError, match="Unsupported auth type"):
        build_auth(42, "user", "pass")


def test_auth_method_name():
    assert auth_method_name(None) == "none"
    assert auth_method_name("digest") == "digest"
    assert auth_method_name(AuthConfig(method="certificate")) == "certificate"
    assert auth_method_name(httpx.BasicAuth("u", "p")) == "custom"


def test_oauth_bearer_sets_header():
    auth = OAuthBearerAuth(token="my-token")
    request = httpx.Request("GET", "http://localhost:8000/")
    flow = auth.auth_flow(request)
    prepared = next(flow)
    assert prepared.headers["Authorization"] == "Bearer my-token"


def test_kerberos_without_dependency_raises_install_hint(monkeypatch):
    monkeypatch.setitem(sys.modules, "spnego", None)
    with pytest.raises(ImportError, match=r"mlclient\[kerberos\]"):
        build_auth(AuthConfig(method="kerberos"), "user", "pass")


def test_kerberos_with_dependency_builds_auth(monkeypatch):
    monkeypatch.setitem(sys.modules, "spnego", _FakeSpnego())
    config = AuthConfig(method="kerberos", hostname="ml.example.com")
    auth = build_auth(config, "user", "pass")
    assert isinstance(auth, KerberosAuth)


def test_kerberos_passes_through_when_no_challenge(monkeypatch):
    monkeypatch.setitem(sys.modules, "spnego", _FakeSpnego())
    auth = KerberosAuth()
    request = httpx.Request("GET", "http://ml.example.com:8000/")

    flow = auth.auth_flow(request)
    prepared = next(flow)
    ok = httpx.Response(httpx.codes.OK, request=prepared)
    with pytest.raises(StopIteration):
        flow.send(ok)

    assert "Authorization" not in prepared.headers


def test_kerberos_negotiate_handshake(monkeypatch):
    spnego = _FakeSpnego()
    monkeypatch.setitem(sys.modules, "spnego", spnego)
    auth = KerberosAuth(hostname="ml.example.com")
    request = httpx.Request("GET", "http://ml.example.com:8000/")

    flow = auth.auth_flow(request)
    first = next(flow)
    challenge = httpx.Response(
        httpx.codes.UNAUTHORIZED,
        headers={"WWW-Authenticate": "Negotiate"},
        request=first,
    )
    retried = flow.send(challenge)

    assert retried.headers["Authorization"] == "Negotiate " + _b64("client-token")
    assert spnego.context.spn == "HTTP/ml.example.com"
    assert spnego.protocol == "kerberos"

    server_token = base64.b64encode(b"server-token").decode("ascii")
    success = httpx.Response(
        httpx.codes.OK,
        headers={"WWW-Authenticate": f"Negotiate {server_token}"},
        request=retried,
    )
    with pytest.raises(StopIteration):
        flow.send(success)

    assert spnego.context.received == b"server-token"


def test_kerberos_mutual_auth_fails_without_server_token(monkeypatch):
    spnego = _FakeSpnego(complete_after_step=False)
    monkeypatch.setitem(sys.modules, "spnego", spnego)
    auth = KerberosAuth(hostname="ml.example.com")
    request = httpx.Request("GET", "http://ml.example.com:8000/")

    flow = auth.auth_flow(request)
    first = next(flow)
    challenge = httpx.Response(
        httpx.codes.UNAUTHORIZED,
        headers={"WWW-Authenticate": "Negotiate"},
        request=first,
    )
    retried = flow.send(challenge)
    success = httpx.Response(httpx.codes.OK, request=retried)

    with pytest.raises(httpx.RequestError, match="Mutual authentication failed"):
        flow.send(success)


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("ascii")).decode("ascii")


class _FakeSpnegoContext:
    def __init__(self, complete_after_step: bool):
        self._complete_after_step = complete_after_step
        self.spn: str | None = None
        self.received: bytes | None = None
        self.complete = False

    def step(self, in_token: bytes | None = None) -> bytes | None:
        if in_token is None:
            self.complete = self._complete_after_step
            return b"client-token"
        self.received = in_token
        self.complete = True
        return None


class _FakeSpnego(types.ModuleType):
    def __init__(self, complete_after_step: bool = True):
        super().__init__("spnego")
        self._complete_after_step = complete_after_step
        self.context: _FakeSpnegoContext | None = None

    def client(self, hostname, service, protocol):
        self.context = _FakeSpnegoContext(self._complete_after_step)
        self.context.spn = f"{service}/{hostname}"
        self.protocol = protocol
        return self.context

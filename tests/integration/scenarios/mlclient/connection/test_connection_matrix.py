"""Connection and authentication matrix, end to end against MarkLogic.

Most rows run against the provisioned app servers and assert that the resolved
identity is what each transport and auth combination should yield: credential
methods authenticate as ``admin``, certificate auth maps the client certificate
to its user, OAuth resolves a locally minted JWT, and Kerberos maps a real
ticket to its principal's user. Cloud has no server to run against, so it
exercises the full client token flow against a mocked ``/token`` endpoint.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import jwt
import pytest
import respx

from mlclient import AuthConfig, MLClient
from mlclient.connection import CloudConfig, SSLConfig

CERT_USER = "mlclient-cert-user"


@pytest.fixture
def ca_bundle(certs_dir: Path) -> str:
    return str(certs_dir / "ca.pem")


@pytest.fixture
def client_cert(certs_dir: Path) -> dict:
    return {
        "cert_file": str(certs_dir / "client.pem"),
        "key_file": str(certs_dir / "client-key.pem"),
    }


@pytest.mark.ml_access
class TestPlainHttp:
    @pytest.mark.parametrize(
        ("port", "auth"),
        [
            (8000, "digest"),
            (8003, "basic"),
            (8004, "digestbasic"),
        ],
    )
    def test_authenticates_as_admin(self, port: int, auth: str):
        assert _current_user(port=port, auth=auth) == "admin"

    def test_application_level_auth_uses_default_user(self):
        assert _current_user(port=8005, auth=None) == "admin"


@pytest.mark.ml_access
class TestServerCertificateTls:
    @pytest.mark.parametrize(
        ("port", "auth"),
        [
            (8006, "digest"),
            (8008, "basic"),
        ],
    )
    def test_authenticates_as_admin(self, port: int, auth: str, ca_bundle: str):
        user = _current_user(
            protocol="https",
            port=port,
            auth=auth,
            ssl=SSLConfig(verify=ca_bundle),
        )
        assert user == "admin"


@pytest.mark.ml_access
class TestMutualTls:
    def test_certificate_auth_maps_to_cert_user(
        self,
        ca_bundle: str,
        client_cert: dict,
    ):
        user = _current_user(
            port=8007,
            ssl=SSLConfig(verify=ca_bundle, **client_cert),
        )
        assert user == CERT_USER

    @pytest.mark.parametrize(
        ("port", "auth"),
        [
            (8009, "digest"),
            (8010, "basic"),
        ],
    )
    def test_double_auth_keeps_credential_identity(
        self,
        port: int,
        auth: str,
        ca_bundle: str,
        client_cert: dict,
    ):
        user = _current_user(
            port=port,
            auth=auth,
            ssl=SSLConfig(verify=ca_bundle, **client_cert),
        )
        assert user == "admin"


@pytest.mark.ml_access
class TestOAuth:
    """OAuth resolves a locally minted JWT to its MarkLogic user, offline.

    MarkLogic validates the Bearer token against the shared secret the
    provisioner configured; no external identity provider is involved.
    """

    def test_jwt_resolves_to_token_user(self, oauth_config: dict):
        token = _mint_jwt(oauth_config)
        user = _current_user(
            port=oauth_config["port"],
            auth=AuthConfig(method="oauth", token=token),
            username="",
            password="",
        )
        assert user == oauth_config["username"]


@pytest.mark.ml_access
@pytest.mark.usefixtures("kerberos_ticket")
class TestKerberos:
    """Kerberos maps a real ticket to its MarkLogic user against a live KDC.

    MarkLogic validates the SPNEGO ticket offline against its keytab, so the
    whole flow - kinit, the Negotiate handshake, principal-to-user mapping -
    runs without contacting any external identity service.
    """

    def test_ticket_resolves_to_principal_user(self, kerberos_config: dict):
        user = _current_user(
            port=kerberos_config["port"],
            auth=AuthConfig(method="kerberos"),
            username="",
            password="",
        )
        assert user == kerberos_config["username"]


class TestCloud:
    """Row 10 has no live server; the full client token flow is mocked."""

    BASE_URL = "https://example.marklogic.cloud"
    BASE_PATH = "/ml/example/manage"

    @respx.mock
    def test_token_flow_authorizes_requests(self):
        token_route = respx.post(f"{self.BASE_URL}/token").mock(
            return_value=httpx.Response(200, json={"access_token": "tok-1"}),
        )
        eval_route = respx.post(
            f"{self.BASE_URL}{self.BASE_PATH}/v1/eval",
        ).mock(
            return_value=httpx.Response(
                200,
                headers={"Content-Type": "text/plain"},
                text="admin",
            ),
        )

        with MLClient(
            host="example.marklogic.cloud",
            cloud=CloudConfig(api_key="mk-123", base_path=self.BASE_PATH),
        ) as ml:
            ml.rest.eval.post(xquery="xdmp:get-current-user()")

        assert token_route.call_count == 1
        assert b"key=mk-123" in token_route.calls.last.request.content

        bearer = eval_route.calls.last.request.headers["Authorization"]
        assert bearer == "Bearer tok-1"


def _current_user(**client_kwargs) -> str:
    with MLClient(host="localhost", **client_kwargs) as ml:
        return ml.eval.xquery("xdmp:get-current-user()")


def _mint_jwt(oauth_config: dict) -> str:
    payload = {
        "iss": oauth_config["issuer"],
        oauth_config["username_claim"]: oauth_config["username"],
        oauth_config["role_claim"]: [oauth_config["role"]],
    }
    return jwt.encode(
        payload,
        oauth_config["secret"],
        algorithm=oauth_config["algorithm"],
        headers={"kid": oauth_config["key_id"]},
    )

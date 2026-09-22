from __future__ import annotations

import json

import httpx
import jwt
import pytest
import respx

from tests.integration import conftest as fixtures
from tests.integration.provision import provision
from tests.integration.scenarios.mlclient.connection.test_connection_matrix import (
    _mint_jwt,
)


@pytest.mark.parametrize(
    ("version", "supported"),
    [
        ("10.0-11.1", False),
        ("11.0", False),
        ("11.1.0", False),
        ("11.2.0", True),
        ("11.3.7", True),
        ("12.1.0", True),
    ],
)
@respx.mock
def test_server_version_selects_only_supported_auth_rows(version, supported):
    body = (
        "\r\n--boundary\r\nContent-Type: text/plain\r\n"
        f"X-Primitive: string\r\n\r\n{version}\r\n--boundary--\r\n"
    )
    respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(200, text=body),
    )
    with provision.ManagementSession("localhost", "admin", "admin") as session:
        actual = session.server_version() >= provision.OAUTH_MIN_VERSION
    assert actual is supported
    specs = provision._applicable_specs(oauth_supported=actual)
    assert any(spec.authentication == "oauth" for spec in specs) is supported
    assert any(spec.authentication == "kerberos-ticket" for spec in specs)
    assert len(provision._mtls_server_names(specs)) == 3
    assert len(provision._external_security_specs(specs)) == (2 if supported else 1)


@respx.mock
def test_server_version_does_not_parse_mime_header_as_version():
    respx.post("http://localhost:8000/v1/eval").mock(
        return_value=httpx.Response(
            200,
            text="MIME-Version: 1.0\r\n\r\nnot a version\r\n",
        ),
    )
    with (
        provision.ManagementSession("localhost", "admin", "admin") as session,
        pytest.raises(RuntimeError, match="Could not parse MarkLogic version"),
    ):
        session.server_version()


def test_oauth_config_replaces_stale_settings_and_skips_only_unsupported(tmp_path):
    provision.write_oauth_config(tmp_path, supported=True)
    config = fixtures.oauth_config.__wrapped__(tmp_path)
    token = _mint_jwt(config)
    payload = jwt.decode(
        token,
        bytes.fromhex(config["secret"]),
        algorithms=[config["algorithm"]],
        audience=config["client_id"],
        issuer=config["issuer"],
    )
    assert payload["aud"] == provision.OAUTH_EXTERNAL_SECURITY
    assert payload[config["username_claim"]] == config["username"]

    path = provision.write_oauth_config(tmp_path, supported=False)
    assert json.loads(path.read_text()) == {"supported": False}
    with pytest.raises(pytest.skip.Exception, match=r"11\.2"):
        fixtures.oauth_config.__wrapped__(tmp_path)

    provision.write_oauth_config(tmp_path, supported=True)
    assert fixtures.oauth_config.__wrapped__(tmp_path)["supported"] is True


@pytest.mark.parametrize("fixture", [fixtures.oauth_config, fixtures.kerberos_config])
def test_missing_auth_config_in_provisioned_rig_is_an_error(tmp_path, fixture):
    with pytest.raises(FileNotFoundError):
        fixture.__wrapped__(tmp_path)


def test_broken_oauth_config_is_not_an_unsupported_server(tmp_path):
    (tmp_path / "oauth.json").write_text("{}")
    with pytest.raises(KeyError, match="supported"):
        fixtures.oauth_config.__wrapped__(tmp_path)


@pytest.mark.parametrize("required", [False, True])
def test_missing_certificates_fail_required_rig_and_skip_optional_rig(
    tmp_path,
    monkeypatch,
    required,
):
    monkeypatch.setenv(fixtures.CERTS_DIR_ENV, str(tmp_path))
    monkeypatch.setenv(
        "MLCLIENT_IT_FAIL_ON_MISSING_PREREQUISITES", "1" if required else "0",
    )
    error = pytest.fail.Exception if required else pytest.skip.Exception
    with pytest.raises(error, match="No provisioned certificates"):
        fixtures.certs_dir.__wrapped__()


def test_missing_kerberos_tooling_fails_required_rig(monkeypatch):
    monkeypatch.setenv("MLCLIENT_IT_FAIL_ON_MISSING_PREREQUISITES", "1")
    monkeypatch.setattr(fixtures.shutil, "which", lambda _: None)
    ticket = fixtures.kerberos_ticket.__wrapped__({"principal": "test@LOCAL"})
    with pytest.raises(pytest.fail.Exception, match="kinit or client keytab"):
        next(ticket)

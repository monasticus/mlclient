from __future__ import annotations

import datetime
import logging
import ssl

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from mlclient._options import UNSET
from mlclient.connection import (
    CloudConfig,
    SSLConfig,
    _default_auth,
    _get_ssl_context,
    _resolve_connection,
    _validate_config,
)
from mlclient.exceptions import ConfigError


def test_resolve_http():
    mode = _resolve_connection("http", 8000, None, None)
    assert mode.protocol == "http"
    assert mode.port == 8000
    assert not mode.is_https
    assert not mode.is_mutual_tls
    assert not mode.is_cloud


def test_resolve_https():
    mode = _resolve_connection("https", 8003, None, None)
    assert mode.protocol == "https"
    assert mode.is_https
    assert mode.ssl is not None
    assert not mode.is_mutual_tls


def test_resolve_mutual_tls_forces_https():
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    mode = _resolve_connection(UNSET, 8003, ssl_config, None)
    assert mode.protocol == "https"
    assert mode.is_mutual_tls


def test_resolve_cloud_forces_https_443():
    cloud = CloudConfig(api_key="mk-123", base_path="/ml/example/manage")
    mode = _resolve_connection(UNSET, UNSET, None, cloud)
    assert mode.protocol == "https"
    assert mode.port == 443
    assert mode.is_cloud


def test_resolve_mutual_tls_explicit_http_raises():
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    with pytest.raises(ConfigError):
        _resolve_connection("http", 8003, ssl_config, None)


def test_resolve_cloud_explicit_http_raises():
    cloud = CloudConfig(api_key="mk-123", base_path="/ml/example/manage")
    with pytest.raises(ConfigError):
        _resolve_connection("http", UNSET, None, cloud)


def test_resolve_cloud_explicit_port_raises():
    cloud = CloudConfig(api_key="mk-123", base_path="/ml/example/manage")
    with pytest.raises(ConfigError):
        _resolve_connection(UNSET, 8002, None, cloud)


def test_validate_cloud_with_auth_raises():
    cloud = CloudConfig(api_key="mk-123", base_path="/p")
    mode = _resolve_connection("https", 443, None, cloud)
    with pytest.raises(ConfigError, match="Cloud connection handles authentication"):
        _validate_config(mode, "digest")


def test_validate_cloud_without_auth_ok():
    cloud = CloudConfig(api_key="mk-123", base_path="/p")
    mode = _resolve_connection("https", 443, None, cloud)
    _validate_config(mode, None)


def test_default_auth_http_is_digest():
    mode = _resolve_connection("http", 8000, None, None)
    assert _default_auth(UNSET, mode) == "digest"


def test_default_auth_mutual_tls_is_certificate():
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    mode = _resolve_connection("https", 8003, ssl_config, None)
    assert _default_auth(UNSET, mode) == "certificate"


def test_default_auth_cloud_is_none():
    cloud = CloudConfig(api_key="mk-123", base_path="/p")
    mode = _resolve_connection("https", 443, None, cloud)
    assert _default_auth(UNSET, mode) is None


def test_default_auth_keeps_explicit_choice():
    mode = _resolve_connection("http", 8000, None, None)
    assert _default_auth("basic", mode) == "basic"


def test_validate_certificate_without_client_cert_raises():
    mode = _resolve_connection("https", 8003, None, None)
    with pytest.raises(ConfigError, match="Certificate authentication requires"):
        _validate_config(mode, "certificate")


def test_validate_certificate_with_mutual_tls_ok():
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    mode = _resolve_connection("https", 8003, ssl_config, None)
    _validate_config(mode, "certificate")


def test_validate_double_auth_ok():
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    mode = _resolve_connection("https", 8003, ssl_config, None)
    _validate_config(mode, "digest")


def test_validate_basic_over_http_warns(caplog):
    connection_logger = logging.getLogger("mlclient.connection")
    connection_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level("WARNING", logger="mlclient.connection"):
            _validate_config(_resolve_connection("http", 8000, None, None), "basic")
    finally:
        connection_logger.removeHandler(caplog.handler)
    assert "cleartext" in caplog.text


def test_get_ssl_context_cached():
    assert _get_ssl_context(SSLConfig()) is _get_ssl_context(SSLConfig())


def test_get_ssl_context_verify_false_returns_none():
    assert _get_ssl_context(SSLConfig(verify=False)) is None


def test_get_ssl_context_custom_ca(tmp_path):
    ca_bundle = _write_self_signed_ca(tmp_path)
    context = _get_ssl_context(SSLConfig(verify=str(ca_bundle)))
    assert context is not None
    assert context is _get_ssl_context(SSLConfig(verify=str(ca_bundle)))


def test_get_ssl_context_loads_client_cert(tmp_path):
    cert_file, key_file = _write_client_cert(tmp_path)
    context = _get_ssl_context(
        SSLConfig(cert_file=str(cert_file), key_file=str(key_file)),
    )
    assert context is not None


def test_get_ssl_context_verify_false_with_client_cert_skips_server_checks(tmp_path):
    cert_file, key_file = _write_client_cert(tmp_path)
    ssl_config = SSLConfig(
        verify=False,
        cert_file=str(cert_file),
        key_file=str(key_file),
    )
    context = _get_ssl_context(ssl_config)
    assert context is not None
    assert context.check_hostname is False
    assert context.verify_mode == ssl.CERT_NONE
    assert context is _get_ssl_context(ssl_config)


def test_get_ssl_context_verify_false_presents_client_cert(tmp_path):
    cert_file, key_file = _write_client_cert(tmp_path)
    server_cert_file, server_key_file = _write_client_cert(tmp_path / "server")
    client_context = _get_ssl_context(
        SSLConfig(verify=False, cert_file=str(cert_file), key_file=str(key_file)),
    )
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(server_cert_file, server_key_file)
    server_context.verify_mode = ssl.CERT_REQUIRED
    server_context.load_verify_locations(cert_file)

    peer_cert = _handshake_in_memory(client_context, server_context)

    assert peer_cert["subject"] == ((("commonName", "mlclient-test-client"),),)


def test_validate_cloud_with_client_cert_raises():
    cloud = CloudConfig(api_key="mk-123", base_path="/p")
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    mode = _resolve_connection(UNSET, UNSET, ssl_config, cloud)
    with pytest.raises(ConfigError, match="does not use client certificates"):
        _validate_config(mode, None)


def test_unset_repr():
    assert repr(UNSET) == "UNSET"


def _write_self_signed_ca(tmp_path):
    """Write a self-signed CA bundle for the factory to load."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "mlclient-test-ca")])
    certificate = _self_signed_certificate(key, name)
    ca_bundle = tmp_path / "ca.pem"
    ca_bundle.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return ca_bundle


def _write_client_cert(tmp_path):
    """Write a self-signed client certificate and its key for the factory."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "mlclient-test-client")])
    certificate = _self_signed_certificate(key, name)
    cert_file = tmp_path / "client.pem"
    cert_file.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_file = tmp_path / "client-key.pem"
    key_file.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ),
    )
    return cert_file, key_file


def _self_signed_certificate(key, name):
    return (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc))
        .not_valid_after(datetime.datetime(2040, 1, 1, tzinfo=datetime.timezone.utc))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )


def _handshake_in_memory(client_context, server_context):
    """Handshake over memory buffers; return the client cert the server received."""
    client_in, client_out = ssl.MemoryBIO(), ssl.MemoryBIO()
    server_in, server_out = ssl.MemoryBIO(), ssl.MemoryBIO()
    client = client_context.wrap_bio(client_in, client_out, server_hostname="localhost")
    server = server_context.wrap_bio(server_in, server_out, server_side=True)
    client_done = server_done = False
    while not (client_done and server_done):
        client_done = client_done or _handshake_step(client)
        server_in.write(client_out.read())
        server_done = server_done or _handshake_step(server)
        client_in.write(server_out.read())
    return server.getpeercert()


def _handshake_step(tls_object):
    try:
        tls_object.do_handshake()
    except ssl.SSLWantReadError:
        return False
    return True

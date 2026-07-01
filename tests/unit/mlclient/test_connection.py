from __future__ import annotations

import datetime
import logging

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from mlclient.connection import (
    UNSET,
    CloudConfig,
    SSLConfig,
    default_auth,
    get_ssl_context,
    resolve_connection,
    validate_config,
)
from mlclient.exceptions import ConfigError


def test_resolve_http():
    mode = resolve_connection("http", 8000, None, None)
    assert mode.protocol == "http"
    assert mode.port == 8000
    assert not mode.is_https
    assert not mode.is_mutual_tls
    assert not mode.is_cloud


def test_resolve_https():
    mode = resolve_connection("https", 8003, None, None)
    assert mode.protocol == "https"
    assert mode.is_https
    assert mode.ssl is not None
    assert not mode.is_mutual_tls


def test_resolve_mutual_tls_forces_https():
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    mode = resolve_connection(UNSET, 8003, ssl_config, None)
    assert mode.protocol == "https"
    assert mode.is_mutual_tls


def test_resolve_cloud_forces_https_443():
    cloud = CloudConfig(api_key="mk-123", base_path="/ml/example/manage")
    mode = resolve_connection(UNSET, UNSET, None, cloud)
    assert mode.protocol == "https"
    assert mode.port == 443
    assert mode.is_cloud


def test_resolve_mutual_tls_explicit_http_raises():
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    with pytest.raises(ConfigError):
        resolve_connection("http", 8003, ssl_config, None)


def test_resolve_cloud_explicit_http_raises():
    cloud = CloudConfig(api_key="mk-123", base_path="/ml/example/manage")
    with pytest.raises(ConfigError):
        resolve_connection("http", UNSET, None, cloud)


def test_resolve_cloud_explicit_port_raises():
    cloud = CloudConfig(api_key="mk-123", base_path="/ml/example/manage")
    with pytest.raises(ConfigError):
        resolve_connection(UNSET, 8002, None, cloud)


def test_validate_cloud_with_auth_raises():
    cloud = CloudConfig(api_key="mk-123", base_path="/p")
    mode = resolve_connection("https", 443, None, cloud)
    with pytest.raises(ConfigError, match="Cloud connection handles authentication"):
        validate_config(mode, "digest")


def test_validate_cloud_without_auth_ok():
    cloud = CloudConfig(api_key="mk-123", base_path="/p")
    mode = resolve_connection("https", 443, None, cloud)
    validate_config(mode, None)


def test_default_auth_http_is_digest():
    mode = resolve_connection("http", 8000, None, None)
    assert default_auth(UNSET, mode) == "digest"


def test_default_auth_mutual_tls_is_certificate():
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    mode = resolve_connection("https", 8003, ssl_config, None)
    assert default_auth(UNSET, mode) == "certificate"


def test_default_auth_cloud_is_none():
    cloud = CloudConfig(api_key="mk-123", base_path="/p")
    mode = resolve_connection("https", 443, None, cloud)
    assert default_auth(UNSET, mode) is None


def test_default_auth_keeps_explicit_choice():
    mode = resolve_connection("http", 8000, None, None)
    assert default_auth("basic", mode) == "basic"


def test_validate_certificate_without_client_cert_raises():
    mode = resolve_connection("https", 8003, None, None)
    with pytest.raises(ConfigError, match="Certificate authentication requires"):
        validate_config(mode, "certificate")


def test_validate_certificate_with_mutual_tls_ok():
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    mode = resolve_connection("https", 8003, ssl_config, None)
    validate_config(mode, "certificate")


def test_validate_double_auth_ok():
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    mode = resolve_connection("https", 8003, ssl_config, None)
    validate_config(mode, "digest")


def test_validate_basic_over_http_warns(caplog):
    connection_logger = logging.getLogger("mlclient.connection")
    connection_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level("WARNING", logger="mlclient.connection"):
            validate_config(resolve_connection("http", 8000, None, None), "basic")
    finally:
        connection_logger.removeHandler(caplog.handler)
    assert "cleartext" in caplog.text


def test_get_ssl_context_cached():
    assert get_ssl_context(SSLConfig()) is get_ssl_context(SSLConfig())


def test_get_ssl_context_verify_false_returns_none():
    assert get_ssl_context(SSLConfig(verify=False)) is None


def test_get_ssl_context_custom_ca(tmp_path):
    ca_bundle = _write_self_signed_ca(tmp_path)
    context = get_ssl_context(SSLConfig(verify=str(ca_bundle)))
    assert context is not None
    assert context is get_ssl_context(SSLConfig(verify=str(ca_bundle)))


def test_get_ssl_context_loads_client_cert(tmp_path):
    cert_file, key_file = _write_client_cert(tmp_path)
    context = get_ssl_context(
        SSLConfig(cert_file=str(cert_file), key_file=str(key_file)),
    )
    assert context is not None


def test_validate_cloud_with_client_cert_raises():
    cloud = CloudConfig(api_key="mk-123", base_path="/p")
    ssl_config = SSLConfig(cert_file="/client.pem", key_file="/client-key.pem")
    mode = resolve_connection(UNSET, UNSET, ssl_config, cloud)
    with pytest.raises(ConfigError, match="does not use client certificates"):
        validate_config(mode, None)


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

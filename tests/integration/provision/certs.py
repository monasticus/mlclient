"""Certificate generation for the TLS integration layer.

A single self-signed certificate authority signs both the server certificate
that MarkLogic presents over HTTPS and the client certificate the test suite
presents for mutual TLS. The same CA, written out as a PEM bundle, is what the
client passes to ``SSLConfig(verify=...)`` to trust that server certificate.

The module is pure: it produces PEM bytes and writes them to a directory. It
has no dependency on a running MarkLogic instance, so it is exercised directly
by unit tests.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

_NOT_BEFORE = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
_NOT_AFTER = datetime.datetime(2040, 1, 1, tzinfo=datetime.timezone.utc)
_KEY_SIZE = 2048


@dataclass(frozen=True)
class KeyPair:
    """A certificate and its private key, both PEM-encoded."""

    certificate_pem: bytes
    key_pem: bytes


@dataclass(frozen=True)
class CertificateBundle:
    """The full set of certificates for the TLS layer.

    ``ca`` signs both leaves; its certificate PEM is the CA bundle the client
    trusts. ``server`` is installed into MarkLogic; ``client`` is presented by
    the test suite for mutual TLS, its CN matching an ML user.
    """

    ca: KeyPair
    server: KeyPair
    client: KeyPair
    client_common_name: str


def build_certificate_bundle(
    server_host: str,
    client_common_name: str,
) -> CertificateBundle:
    """Create a CA and the server and client certificates it signs."""
    ca_key = _generate_key()
    ca_certificate = _build_ca_certificate(ca_key)

    server = _issue_leaf(
        ca_key,
        ca_certificate,
        common_name=server_host,
        subject_alt_names=[x509.DNSName(server_host)],
        extended_usage=x509.ExtendedKeyUsageOID.SERVER_AUTH,
    )
    client = _issue_leaf(
        ca_key,
        ca_certificate,
        common_name=client_common_name,
        subject_alt_names=[],
        extended_usage=x509.ExtendedKeyUsageOID.CLIENT_AUTH,
    )

    return CertificateBundle(
        ca=KeyPair(_encode_certificate(ca_certificate), _encode_key(ca_key)),
        server=server,
        client=client,
        client_common_name=client_common_name,
    )


def write_certificate_bundle(
    bundle: CertificateBundle,
    target_dir: Path,
) -> dict[str, Path]:
    """Write every PEM in the bundle to ``target_dir`` and return their paths."""
    target_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "ca.pem": bundle.ca.certificate_pem,
        "ca-key.pem": bundle.ca.key_pem,
        "server.pem": bundle.server.certificate_pem,
        "server-key.pem": bundle.server.key_pem,
        "client.pem": bundle.client.certificate_pem,
        "client-key.pem": bundle.client.key_pem,
    }
    written = {}
    for name, content in files.items():
        path = target_dir / name
        path.write_bytes(content)
        written[name] = path
    return written


def _build_ca_certificate(ca_key: rsa.RSAPrivateKey) -> x509.Certificate:
    name = _name("mlclient-integration-ca")
    return (
        _base_builder(name, name, ca_key.public_key())
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )


def _issue_leaf(
    ca_key: rsa.RSAPrivateKey,
    ca_certificate: x509.Certificate,
    common_name: str,
    subject_alt_names: list[x509.GeneralName],
    extended_usage: x509.ObjectIdentifier,
) -> KeyPair:
    key = _generate_key()
    builder = (
        _base_builder(_name(common_name), ca_certificate.subject, key.public_key())
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([extended_usage]),
            critical=False,
        )
    )
    if subject_alt_names:
        builder = builder.add_extension(
            x509.SubjectAlternativeName(subject_alt_names),
            critical=False,
        )
    certificate = builder.sign(ca_key, hashes.SHA256())
    return KeyPair(_encode_certificate(certificate), _encode_key(key))


def _base_builder(
    subject: x509.Name,
    issuer: x509.Name,
    public_key: rsa.RSAPublicKey,
) -> x509.CertificateBuilder:
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(_NOT_BEFORE)
        .not_valid_after(_NOT_AFTER)
    )


def _name(common_name: str) -> x509.Name:
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])


def _generate_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=_KEY_SIZE)


def _encode_certificate(certificate: x509.Certificate) -> bytes:
    return certificate.public_bytes(serialization.Encoding.PEM)


def _encode_key(key: rsa.RSAPrivateKey) -> bytes:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

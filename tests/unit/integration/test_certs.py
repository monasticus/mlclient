from __future__ import annotations

import ssl

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509.oid import ExtensionOID, NameOID

from tests.integration.provision.certs import (
    build_certificate_bundle,
    write_certificate_bundle,
)


def _load(certificate_pem: bytes) -> x509.Certificate:
    return x509.load_pem_x509_certificate(certificate_pem)


def _common_name(certificate: x509.Certificate) -> str:
    return certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value


def test_ca_is_marked_as_certificate_authority():
    bundle = build_certificate_bundle("ml.local", "test-client")
    ca = _load(bundle.ca.certificate_pem)
    constraints = ca.extensions.get_extension_for_oid(
        ExtensionOID.BASIC_CONSTRAINTS,
    ).value
    assert constraints.ca is True


def test_leaves_are_signed_by_the_ca():
    bundle = build_certificate_bundle("ml.local", "test-client")
    ca = _load(bundle.ca.certificate_pem)
    for leaf_pem in (bundle.server.certificate_pem, bundle.client.certificate_pem):
        leaf = _load(leaf_pem)
        assert leaf.issuer == ca.subject
        ca.public_key().verify(
            leaf.signature,
            leaf.tbs_certificate_bytes,
            padding.PKCS1v15(),
            leaf.signature_hash_algorithm,
        )


def test_server_certificate_carries_host_subject_alt_name():
    bundle = build_certificate_bundle("ml.example.com", "test-client")
    server = _load(bundle.server.certificate_pem)
    alt_names = server.extensions.get_extension_for_oid(
        ExtensionOID.SUBJECT_ALTERNATIVE_NAME,
    ).value
    assert alt_names.get_values_for_type(x509.DNSName) == ["ml.example.com"]


def test_client_certificate_common_name_matches_requested_user():
    bundle = build_certificate_bundle("ml.local", "cert-user")
    assert bundle.client_common_name == "cert-user"
    assert _common_name(_load(bundle.client.certificate_pem)) == "cert-user"


def test_ca_bundle_loads_into_an_ssl_context(tmp_path):
    bundle = build_certificate_bundle("ml.local", "cert-user")
    files = write_certificate_bundle(bundle, tmp_path)
    context = ssl.create_default_context(cafile=str(files["ca.pem"]))
    assert context.get_ca_certs()


def test_write_emits_every_pem(tmp_path):
    bundle = build_certificate_bundle("ml.local", "cert-user")
    files = write_certificate_bundle(bundle, tmp_path)
    assert set(files) == {
        "ca.pem",
        "ca-key.pem",
        "server.pem",
        "server-key.pem",
        "client.pem",
        "client-key.pem",
    }
    for path in files.values():
        assert path.read_bytes()

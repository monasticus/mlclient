from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

CERTS_DIR_ENV = "MLCLIENT_IT_CERTS_DIR"
DEFAULT_CERTS_DIR = "tests/integration/.certs"
OAUTH_CONFIG_FILE = "oauth.json"
KERBEROS_CONFIG_FILE = "kerberos.json"

_KRB_DIR = Path(__file__).parent / ".krb"
_KRB5_CONFIG = Path(__file__).parent / "krb5" / "krb5.conf"
_CLIENT_KEYTAB = _KRB_DIR / "client.keytab"


def _missing_prerequisite(message: str) -> None:
    """Fail an explicitly required CI rig; skip an unavailable optional local rig."""
    if os.environ.get("MLCLIENT_IT_REQUIRED") == "1":
        pytest.fail(message)
    pytest.skip(message)


@pytest.fixture(scope="session")
def certs_dir() -> Path:
    """Directory holding the certificates the provisioner generated.

    The provisioner writes the CA bundle and the client certificate/key here.
    CI mounts the provisioner volume at this path; locally it defaults to a
    directory the provisioning step populates.
    """
    path = Path(os.environ.get(CERTS_DIR_ENV, DEFAULT_CERTS_DIR))
    if not (path / "ca.pem").exists():
        _missing_prerequisite(
            f"No provisioned certificates at {path} (set {CERTS_DIR_ENV})",
        )
    return path


@pytest.fixture(scope="session")
def oauth_config(certs_dir: Path) -> dict:
    """OAuth parameters the provisioner wrote, used to mint a matching JWT."""
    path = certs_dir / OAUTH_CONFIG_FILE
    config = json.loads(path.read_text())
    if config["supported"] is False:
        pytest.skip("OAuth JWT Resource Server requires MarkLogic 11.2+")
    return config


@pytest.fixture(scope="session")
def kerberos_config(certs_dir: Path) -> dict:
    """Kerberos parameters the provisioner wrote for the live KDC test."""
    path = certs_dir / KERBEROS_CONFIG_FILE
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def kerberos_ticket(kerberos_config: dict):
    """Obtain a ticket-granting ticket for the client principal via kinit.

    The KDC exported the client keytab to a shared directory; kinit places the
    ticket in a test-scoped credential cache so the Kerberos client picks it up.
    Skips when the Kerberos tooling or keytab is unavailable, keeping the suite
    runnable without the live KDC.
    """
    kinit = shutil.which("kinit")
    if kinit is None or not _CLIENT_KEYTAB.exists():
        _missing_prerequisite("kinit or client keytab unavailable (no live KDC)")

    # The keytab lives in a bind mount the KDC container owns as root, so the
    # credential cache goes to a writable temp directory instead; kinit cannot
    # create the cache file next to a root-owned keytab.
    with tempfile.TemporaryDirectory(prefix="mlclient-krb5-") as cache_dir:
        cache = Path(cache_dir) / "krb5cc_mlclient"
        env = {
            **os.environ,
            "KRB5_CONFIG": str(_KRB5_CONFIG),
            "KRB5CCNAME": f"FILE:{cache}",
        }
        subprocess.run(
            [kinit, "-k", "-t", str(_CLIENT_KEYTAB), kerberos_config["principal"]],
            env=env,
            check=True,
        )
        previous = {key: os.environ.get(key) for key in ("KRB5_CONFIG", "KRB5CCNAME")}
        os.environ.update(KRB5_CONFIG=env["KRB5_CONFIG"], KRB5CCNAME=env["KRB5CCNAME"])
        yield
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

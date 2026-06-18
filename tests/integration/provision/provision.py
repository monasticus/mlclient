"""Provision the MarkLogic instance for the connection/auth integration matrix.

Run once after MarkLogic is up. It creates one REST app server per matrix row,
each combining a transport (plain HTTP, server-certificate HTTPS, or mutual TLS)
with an authentication method; ``SERVER_SPECS`` is the full list.

Row 1 (HTTP digest) reuses the built-in App-Services server on 8000. Row 10
(Cloud) is client-side only and is covered by a respx unit test, not here.

The TLS rows share one certificate authority. It signs the server certificate
installed into MarkLogic and the client certificate the suite presents for
mutual TLS; its PEM is the bundle the client trusts. Generated certificates are
written to a directory the test suite reads.

Most configuration is plain Management REST. Only two operations have no REST
form and are done through ``/v1/eval``: installing externally generated PKI
material into the certificate template, and trusting the client CA on the
mutual-TLS servers.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from .certs import CertificateBundle, build_certificate_bundle, write_certificate_bundle

CERT_USER = "mlclient-cert-user"
TEMPLATE_NAME = "mlclient-it"
CONTENT_DATABASE = "Documents"
MODULES_DATABASE = "Modules"

OAUTH_PORT = 8011
OAUTH_EXTERNAL_SECURITY = "mlclient-it-oauth"
OAUTH_ROLE = "mlclient-it-oauth-role"
OAUTH_USER = "mlclient-oauth-user"
OAUTH_ISSUER = "mlclient-it"
OAUTH_KEY_ID = "mlclient-it-key"
OAUTH_SECRET = "mlclient-it-shared-secret-please-rotate"
OAUTH_ALGORITHM = "HS256"
OAUTH_USERNAME_CLAIM = "username"
OAUTH_ROLE_CLAIM = "roles"
OAUTH_CONFIG_FILE = "oauth.json"

KERBEROS_PORT = 8012
KERBEROS_EXTERNAL_SECURITY = "mlclient-it-kerberos"
KERBEROS_USER = "mlclient-kerberos-user"
KERBEROS_CONFIG_FILE = "kerberos.json"

DEFAULT_HOST = "localhost"
DEFAULT_REST_PORT = 8000
DEFAULT_ADMIN_PORT = 8001
DEFAULT_MANAGE_PORT = 8002
DEFAULT_HEALTH_PORT = 7997
DEFAULT_CERTS_DIR = "/certs"
READINESS_TIMEOUT = 240
READINESS_POLL = 5.0
REQUEST_ATTEMPTS = 5
STABLE_READS_REQUIRED = 3


@dataclass(frozen=True)
class ServerSpec:
    """One app server to provision, named after the matrix row it serves."""

    name: str
    port: int
    tls: bool
    authentication: str
    require_client_cert: bool = False
    external_security: str | None = None


SERVER_SPECS = (
    ServerSpec("mlclient-it-http-basic", 8003, tls=False, authentication="basic"),
    ServerSpec(
        "mlclient-it-http-digestbasic",
        8004,
        tls=False,
        authentication="digestbasic",
    ),
    ServerSpec(
        "mlclient-it-http-none",
        8005,
        tls=False,
        authentication="application-level",
    ),
    ServerSpec("mlclient-it-https-digest", 8006, tls=True, authentication="digest"),
    ServerSpec("mlclient-it-https-basic", 8008, tls=True, authentication="basic"),
    ServerSpec(
        "mlclient-it-mtls-cert",
        8007,
        tls=True,
        authentication="certificate",
        require_client_cert=True,
    ),
    ServerSpec(
        "mlclient-it-mtls-digest",
        8009,
        tls=True,
        authentication="digest",
        require_client_cert=True,
    ),
    ServerSpec(
        "mlclient-it-mtls-basic",
        8010,
        tls=True,
        authentication="basic",
        require_client_cert=True,
    ),
    ServerSpec(
        "mlclient-it-oauth",
        OAUTH_PORT,
        tls=False,
        authentication="oauth",
        external_security=OAUTH_EXTERNAL_SECURITY,
    ),
    ServerSpec(
        "mlclient-it-kerberos",
        KERBEROS_PORT,
        tls=False,
        authentication="kerberos-ticket",
        external_security=KERBEROS_EXTERNAL_SECURITY,
    ),
)


def main() -> int:
    """Provision MarkLogic for the integration matrix."""
    args = _parse_args()
    with ManagementSession(
        args.host,
        args.username,
        args.password,
        args.health_port,
    ) as session:
        session.wait_until_ready()

        bundle = build_certificate_bundle(
            server_host=args.host,
            client_common_name=CERT_USER,
        )
        write_certificate_bundle(bundle, Path(args.certs_dir))

        session.ensure_cert_user(CERT_USER)
        session.ensure_certificate_template(TEMPLATE_NAME)
        session.install_host_certificate(TEMPLATE_NAME, bundle)
        session.ensure_oauth_external_security()
        session.ensure_kerberos_external_security(args.kerberos_principal)

        for spec in SERVER_SPECS:
            session.create_rest_server(spec)
            session.configure_server(spec, TEMPLATE_NAME)

        session.bind_client_certificate_authority(bundle, _mtls_server_names())
        for spec in _external_security_specs():
            session.bind_external_security(spec)
        write_oauth_config(Path(args.certs_dir))
        write_kerberos_config(Path(args.certs_dir), args.kerberos_principal)
        session.wait_until_stable(args.admin_port)
    print("Provisioning complete.")
    return 0


def _mtls_server_names() -> list[str]:
    return [spec.name for spec in SERVER_SPECS if spec.require_client_cert]


def _external_security_specs() -> list[ServerSpec]:
    return [spec for spec in SERVER_SPECS if spec.external_security]


def write_oauth_config(target_dir: Path) -> Path:
    """Write the OAuth parameters the test suite needs to mint a JWT."""
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / OAUTH_CONFIG_FILE
    path.write_text(
        json.dumps(
            {
                "port": OAUTH_PORT,
                "issuer": OAUTH_ISSUER,
                "key_id": OAUTH_KEY_ID,
                "secret": OAUTH_SECRET,
                "algorithm": OAUTH_ALGORITHM,
                "username_claim": OAUTH_USERNAME_CLAIM,
                "role_claim": OAUTH_ROLE_CLAIM,
                "username": OAUTH_USER,
                "role": OAUTH_ROLE,
            },
        ),
    )
    return path


def write_kerberos_config(target_dir: Path, principal: str) -> Path:
    """Write the Kerberos parameters the test suite needs to authenticate."""
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / KERBEROS_CONFIG_FILE
    path.write_text(
        json.dumps(
            {
                "port": KERBEROS_PORT,
                "principal": principal,
                "username": KERBEROS_USER,
            },
        ),
    )
    return path


class ManagementSession:
    """Drives MarkLogic's Management REST API and admin XQuery over digest auth."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        health_port: int = DEFAULT_HEALTH_PORT,
    ):
        self._host = host
        self._client = httpx.Client(
            auth=httpx.DigestAuth(username, password),
            timeout=60.0,
        )
        self._rest = f"http://{host}:{DEFAULT_REST_PORT}"
        self._manage = f"http://{host}:{DEFAULT_MANAGE_PORT}"
        self._health_url = f"http://{host}:{health_port}/LATEST/healthcheck"

    def __enter__(self) -> ManagementSession:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._client.close()

    def wait_until_ready(self) -> None:
        """Block until the health check endpoint reports the host is up."""
        self._await_health()

    def _await_health(self) -> None:
        deadline = time.monotonic() + READINESS_TIMEOUT
        while time.monotonic() < deadline:
            try:
                if self._client.get(self._health_url).status_code == httpx.codes.OK:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(READINESS_POLL)
        msg = f"MarkLogic did not become ready within {READINESS_TIMEOUT}s"
        raise TimeoutError(msg)

    def ensure_cert_user(self, common_name: str) -> None:
        """Create the user whose name matches the client certificate CN."""
        self._eval(_CREATE_USER_XQUERY, {"user": common_name})

    def ensure_certificate_template(self, template_name: str) -> None:
        """Create the certificate template shared by every TLS server."""
        response = self._request(
            "POST",
            f"{self._manage}/manage/v2/certificate-templates",
            headers={"Content-Type": "application/json"},
            json={
                "template-name": template_name,
                "template-description": "mlclient integration matrix",
                "key-type": "rsa",
                "key-options": {"key-length": "2048"},
                "req": {
                    "version": "0",
                    "subject": {
                        "organizationName": "mlclient",
                        "commonName": self._host,
                    },
                },
            },
        )
        _expect(response, httpx.codes.CREATED, httpx.codes.CONFLICT)

    def install_host_certificate(
        self,
        template_name: str,
        bundle: CertificateBundle,
    ) -> None:
        """Install the CA-signed server certificate into the template."""
        self._eval(
            _INSTALL_HOST_CERT_XQUERY,
            {
                "template": template_name,
                "cert": bundle.server.certificate_pem.decode(),
                "key": bundle.server.key_pem.decode(),
            },
        )

    def create_rest_server(self, spec: ServerSpec) -> None:
        """Create a REST API instance so the server hosts ``/v1/*``."""
        response = self._request(
            "POST",
            f"{self._manage}/v1/rest-apis",
            headers={"Content-Type": "application/json"},
            json={
                "rest-api": {
                    "name": spec.name,
                    "port": spec.port,
                    "database": CONTENT_DATABASE,
                    "modules-database": MODULES_DATABASE,
                },
            },
        )
        _expect(response, httpx.codes.CREATED, httpx.codes.CONFLICT)

    def configure_server(self, spec: ServerSpec, template_name: str) -> None:
        """Set a server's authentication and TLS properties.

        Servers backed by external security have their authentication set when
        the external-security object is bound, so they are skipped here.
        """
        if spec.external_security:
            return
        properties: dict[str, object] = {"authentication": spec.authentication}
        if spec.authentication == "application-level":
            properties["default-user"] = "admin"
        if spec.tls:
            properties["ssl-certificate-template"] = template_name
        if spec.require_client_cert:
            properties["ssl-require-client-certificate"] = True
        response = self._request(
            "PUT",
            f"{self._manage}/manage/v2/servers/{spec.name}/properties",
            params={"group-id": "Default"},
            headers={"Content-Type": "application/json"},
            json=properties,
        )
        _expect(response, httpx.codes.NO_CONTENT)

    def bind_client_certificate_authority(
        self,
        bundle: CertificateBundle,
        mtls_server_names: list[str],
    ) -> None:
        """Trust the client CA on every mutual-TLS server."""
        if not mtls_server_names:
            return
        self._eval(
            _BIND_CLIENT_CA_XQUERY,
            {
                "ca": bundle.ca.certificate_pem.decode(),
                "servers": ",".join(mtls_server_names),
            },
        )

    def ensure_oauth_external_security(self) -> None:
        """Create the OAuth external security object and its role.

        The role's external name matches the role claim the test puts in the
        JWT, so MarkLogic grants it to the temporary user the token resolves to.
        """
        self._eval(
            _CREATE_OAUTH_EXTERNAL_SECURITY_XQUERY,
            {
                "name": OAUTH_EXTERNAL_SECURITY,
                "role": OAUTH_ROLE,
                "issuer": OAUTH_ISSUER,
                "username-attribute": OAUTH_USERNAME_CLAIM,
                "role-attribute": OAUTH_ROLE_CLAIM,
                "algorithm": OAUTH_ALGORITHM,
                "key-id": OAUTH_KEY_ID,
                "secret": OAUTH_SECRET,
            },
        )

    def ensure_kerberos_external_security(self, principal: str) -> None:
        """Create the Kerberos external security object, role and user.

        The user's external name is the Kerberos principal the client presents,
        so MarkLogic maps the authenticated ticket to that user.
        """
        self._eval(
            _CREATE_KERBEROS_EXTERNAL_SECURITY_XQUERY,
            {
                "name": KERBEROS_EXTERNAL_SECURITY,
                "user": KERBEROS_USER,
                "principal": principal,
            },
        )

    def bind_external_security(self, spec: ServerSpec) -> None:
        """Attach a server's external security object and authentication."""
        self._eval(
            _BIND_EXTERNAL_SECURITY_XQUERY,
            {
                "external-security": spec.external_security,
                "authentication": spec.authentication,
                "server": spec.name,
            },
        )

    def wait_until_stable(self, admin_port: int) -> None:
        """Block until MarkLogic stops restarting from the configuration changes.

        Creating servers and binding certificates each restart MarkLogic. The
        admin restart timestamp changes on every restart, so a run of identical
        reads means the cascade has settled and the app servers are serving.
        """
        url = f"http://{self._host}:{admin_port}/admin/v1/timestamp"
        deadline = time.monotonic() + READINESS_TIMEOUT
        last_timestamp: str | None = None
        stable_reads = 0
        while time.monotonic() < deadline:
            timestamp = self._read_timestamp(url)
            if timestamp is not None and timestamp == last_timestamp:
                stable_reads += 1
                if stable_reads >= STABLE_READS_REQUIRED:
                    return
            else:
                stable_reads = 1 if timestamp is not None else 0
            last_timestamp = timestamp
            time.sleep(READINESS_POLL)
        msg = "MarkLogic did not stabilise after provisioning"
        raise TimeoutError(msg)

    def _read_timestamp(self, url: str) -> str | None:
        try:
            response = self._client.get(url)
        except httpx.HTTPError:
            return None
        if response.status_code != httpx.codes.OK:
            return None
        return response.text.strip()

    def _eval(self, xquery: str, variables: dict[str, str]) -> None:
        response = self._request(
            "POST",
            f"{self._rest}/v1/eval",
            data={"xquery": xquery, "vars": json.dumps(variables)},
        )
        _expect(response, httpx.codes.OK)

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Send a request, retrying across the restarts configuration triggers.

        Creating servers and installing certificates restart MarkLogic, which
        drops in-flight connections. On a transport error the host is given time
        to come back before the request is retried.
        """
        last_error: httpx.HTTPError | None = None
        for _ in range(REQUEST_ATTEMPTS):
            try:
                return self._client.request(method, url, **kwargs)
            except httpx.HTTPError as error:
                last_error = error
                self._await_health()
        if last_error is None:
            msg = "request was never attempted; REQUEST_ATTEMPTS must be positive"
            raise RuntimeError(msg)
        raise last_error


def _expect(response: httpx.Response, *accepted: int) -> None:
    if response.status_code not in accepted:
        msg = (
            f"{response.request.method} {response.request.url} returned "
            f"{response.status_code}, expected {accepted}: {response.text[:500]}"
        )
        raise RuntimeError(msg)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--health-port", type=int, default=DEFAULT_HEALTH_PORT)
    parser.add_argument("--admin-port", type=int, default=DEFAULT_ADMIN_PORT)
    parser.add_argument("--certs-dir", default=DEFAULT_CERTS_DIR)
    parser.add_argument(
        "--kerberos-principal",
        default=os.environ.get(
            "MLCLIENT_IT_KERBEROS_PRINCIPAL",
            "mlclient@MLCLIENT.LOCAL",
        ),
    )
    return parser.parse_args()


_CREATE_USER_XQUERY = """
xquery version "1.0-ml";
import module namespace sec = "http://marklogic.com/xdmp/security"
  at "/MarkLogic/security.xqy";
declare variable $user external;
xdmp:invoke-function(
  function() {
    if (sec:user-exists($user)) then ()
    else sec:create-user($user, "Integration mTLS user", "unused", ("admin"), (), ())
  },
  map:map() => map:with("database", xdmp:security-database())
)
"""

_INSTALL_HOST_CERT_XQUERY = """
xquery version "1.0-ml";
import module namespace pki = "http://marklogic.com/xdmp/pki"
  at "/MarkLogic/pki.xqy";
declare variable $template external;
declare variable $cert external;
declare variable $key external;
xdmp:invoke-function(
  function() {
    let $tid := pki:get-template-by-name($template)/pki:template-id
    return pki:insert-host-certificate($tid, $cert, $key)
  },
  map:map() => map:with("database", xdmp:security-database())
)
"""

_BIND_CLIENT_CA_XQUERY = """
xquery version "1.0-ml";
import module namespace pki = "http://marklogic.com/xdmp/pki"
  at "/MarkLogic/pki.xqy";
import module namespace admin = "http://marklogic.com/xdmp/admin"
  at "/MarkLogic/admin.xqy";
declare variable $ca external;
declare variable $servers external;
xdmp:invoke-function(
  function() {
    let $cert-ids := pki:insert-trusted-certificates($ca)
    let $config := admin:get-configuration()
    let $gid := admin:group-get-id($config, "Default")
    let $updated :=
      fn:fold-left(
        function($cfg, $name) {
          admin:appserver-set-ssl-client-certificate-authorities(
            $cfg, admin:appserver-get-id($cfg, $gid, $name), $cert-ids
          )
        },
        $config,
        fn:tokenize($servers, ",")
      )
    return admin:save-configuration($updated)
  },
  map:map() => map:with("database", xdmp:security-database())
)
"""

_CREATE_OAUTH_EXTERNAL_SECURITY_XQUERY = """
xquery version "1.0-ml";
import module namespace sec = "http://marklogic.com/xdmp/security"
  at "/MarkLogic/security.xqy";
declare variable $name external;
declare variable $role external;
declare variable $issuer external;
declare variable $username-attribute external;
declare variable $role-attribute external;
declare variable $algorithm external;
declare variable $key-id external;
declare variable $secret external;
xdmp:invoke-function(
  function() {
    let $_ :=
      if (sec:role-exists($role)) then ()
      else sec:create-role($role, "Integration OAuth role", (), (), (), (), $role)
    let $oauth-server := sec:oauth-server(
      "Other", "Resource server", $name, "JSON Web Tokens",
      $username-attribute, $role-attribute, (), $issuer, $algorithm,
      $key-id, $secret
    )
    return
      try {
        sec:create-external-security(
          $name, "Integration OAuth external security", "oauth", 300, "oauth",
          (), (), $oauth-server
        )
      } catch ($e) {
        if ($e/error:code = "SEC-EXTERNALSECURITYEXISTS") then ()
        else xdmp:rethrow()
      }
  },
  map:map() => map:with("database", xdmp:security-database())
)
"""

_CREATE_KERBEROS_EXTERNAL_SECURITY_XQUERY = """
xquery version "1.0-ml";
import module namespace sec = "http://marklogic.com/xdmp/security"
  at "/MarkLogic/security.xqy";
declare variable $name external;
declare variable $user external;
declare variable $principal external;
xdmp:invoke-function(
  function() {
    let $_ :=
      if (sec:user-exists($user)) then sec:user-set-external-names($user, $principal)
      else sec:create-user(
        $user, "Integration Kerberos user", "unused", ("admin"), (), (), $principal
      )
    return
      try {
        sec:create-external-security(
          $name, "Integration Kerberos external security", "kerberos", 300,
          "internal", (), ()
        )
      } catch ($e) {
        if ($e/error:code = "SEC-EXTERNALSECURITYEXISTS") then ()
        else xdmp:rethrow()
      }
  },
  map:map() => map:with("database", xdmp:security-database())
)
"""

_BIND_EXTERNAL_SECURITY_XQUERY = """
xquery version "1.0-ml";
import module namespace admin = "http://marklogic.com/xdmp/admin"
  at "/MarkLogic/admin.xqy";
declare variable $external-security external;
declare variable $authentication external;
declare variable $server external;
xdmp:invoke-function(
  function() {
    let $config := admin:get-configuration()
    let $gid := admin:group-get-id($config, "Default")
    let $sid := admin:appserver-get-id($config, $gid, $server)
    let $updated := admin:appserver-set-external-security(
      $config, $sid, $external-security, fn:false(), $authentication
    )
    return admin:save-configuration($updated)
  },
  map:map() => map:with("database", xdmp:security-database())
)
"""


if __name__ == "__main__":
    sys.exit(main())

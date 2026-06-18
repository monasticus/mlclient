"""The Authentication module.

This module models the application layer of a MarkLogic connection: how the
client proves its identity, independent of the transport. It exports:

    * AuthConfig
        Data a specific auth mechanism needs beyond the shared user identity.
    * build_auth
        Resolve an auth parameter to an httpx.Auth instance.
    * OAuthBearerAuth
        OAuth 2.0 Bearer token authentication.
    * KerberosAuth
        Kerberos/SPNEGO (Negotiate) authentication over pyspnego.
    * MarkLogicCloudAuth
        MarkLogic Cloud API key exchanged for a Bearer token, with refresh.

``username`` / ``password`` model the MarkLogic user identity. That identity is
shared across the credential methods and independent of the wire mechanism - the
same user can be presented as basic or digest by flipping ``auth`` without
touching the credential - so it lives on the client (and at the root of a YAML
environment, inherited per server) rather than on any one method.

``auth`` selects the wire mechanism. Most mechanisms are selectable by name
alone: the credential ones (``"basic"``, ``"digest"``, ``"digestbasic"``) draw
on the shared identity, while ``"certificate"`` and ``"kerberos"`` draw their
identity from elsewhere (the TLS client certificate, the ambient ticket cache)
and need no extra data.

``AuthConfig`` carries the data a specific mechanism needs beyond the shared
identity: OAuth's token (which has no default, so ``AuthConfig`` is the only way
to select OAuth) or a Kerberos SPN override. It is not a credential store -
basic/digest credentials never pass through it.
"""

from __future__ import annotations

import base64
import logging
import ssl
from typing import Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

_TokenVerify = Union[bool, str, ssl.SSLContext]

logger = logging.getLogger(__name__)

CREDENTIAL_AUTH_SHORTCUTS = ("basic", "digest", "digestbasic")
DEFAULTED_AUTH_SHORTCUTS = ("certificate", "kerberos")
AUTH_SHORTCUTS = CREDENTIAL_AUTH_SHORTCUTS + DEFAULTED_AUTH_SHORTCUTS
CONFIG_AUTH_METHODS = ("certificate", "oauth", "kerberos")

AuthParam = Union[str, httpx.Auth, "AuthConfig", None]


class AuthConfig(BaseModel):
    """Data a specific auth mechanism needs beyond the shared user identity.

    Holds OAuth's token or a Kerberos SPN override (``service`` / ``hostname``).
    It is not a credential store: basic/digest identity comes from the client's
    ``username`` / ``password``, never from here.
    """

    method: str
    token: Optional[str] = None
    service: str = "HTTP"
    hostname: Optional[str] = None


def auth_method_name(
    auth: AuthParam,
) -> str:
    """Return the canonical auth method name for an auth parameter.

    Parameters
    ----------
    auth : str | httpx.Auth | AuthConfig | None
        An auth parameter.

    Returns
    -------
    str
        The method name: a shortcut value, an AuthConfig method, ``"none"`` for
        None, or ``"custom"`` for a custom httpx.Auth instance.
    """
    if auth is None:
        return "none"
    if isinstance(auth, AuthConfig):
        return auth.method
    if isinstance(auth, str):
        return auth
    return "custom"


def build_auth(
    auth: AuthParam,
    username: str,
    password: str,
) -> httpx.Auth | None:
    """Resolve an auth parameter to an httpx.Auth instance.

    Parameters
    ----------
    auth : str | httpx.Auth | AuthConfig | None
        A string shortcut, a ready httpx.Auth, an AuthConfig for methods needing
        extra data, or None for application-level auth.
    username : str
        A username for credential-based methods.
    password : str
        A password for credential-based methods.

    Returns
    -------
    httpx.Auth | None
        An httpx authentication handler, or None when no HTTP auth header is
        applied (application-level or certificate auth).

    Raises
    ------
    ValueError
        If a string shortcut or AuthConfig method is not recognized.
    TypeError
        If the auth parameter is of an unsupported type.
    """
    if auth is None:
        return None
    if isinstance(auth, httpx.Auth):
        return auth
    if isinstance(auth, str):
        return _build_from_shortcut(auth, username, password)
    if isinstance(auth, AuthConfig):
        return _build_from_config(auth)
    msg = f"Unsupported auth type: {type(auth)}"
    raise TypeError(msg)


def _build_from_shortcut(
    auth: str,
    username: str,
    password: str,
) -> httpx.Auth | None:
    """Build an httpx.Auth from a string shortcut.

    Credential shortcuts use ``username`` / ``password``. The defaulted
    shortcuts (certificate, kerberos) select a method that needs no extra data
    and resolve through the same path as an ``AuthConfig`` with default fields.
    """
    if auth == "basic":
        return httpx.BasicAuth(username, password)
    if auth in ("digest", "digestbasic"):
        return httpx.DigestAuth(username, password)
    if auth in DEFAULTED_AUTH_SHORTCUTS:
        return _build_from_config(AuthConfig(method=auth))
    msg = (
        f"Unknown auth shortcut: {auth!r}. "
        f"Only {', '.join(repr(s) for s in AUTH_SHORTCUTS)} "
        f"are valid as strings."
    )
    raise ValueError(msg)


def _build_from_config(
    config: AuthConfig,
) -> httpx.Auth | None:
    """Build an httpx.Auth from an AuthConfig."""
    if config.method == "certificate":
        return None
    if config.method == "oauth":
        return OAuthBearerAuth(token=config.token)
    if config.method == "kerberos":
        return _build_kerberos_auth(config)
    msg = f"Unknown auth method: {config.method!r}"
    raise ValueError(msg)


def _build_kerberos_auth(
    config: AuthConfig,
) -> httpx.Auth:
    """Build a Kerberos httpx.Auth from an AuthConfig.

    Kerberos support is an optional dependency. The import is verified here, at
    client creation, so a missing dependency fails early with an install hint.
    """
    _import_spnego()
    return KerberosAuth(service=config.service, hostname=config.hostname)


def _import_spnego():
    """Import the optional spnego dependency, or raise an install hint."""
    try:
        import spnego  # noqa: PLC0415
    except ImportError as exc:
        msg = (
            "Kerberos authentication requires the optional 'pyspnego' "
            "dependency. Install it with: pip install mlclient[kerberos]"
        )
        raise ImportError(msg) from exc
    return spnego


class OAuthBearerAuth(httpx.Auth):
    """OAuth 2.0 Bearer token authentication."""

    def __init__(
        self,
        token: str,
    ):
        """Initialize OAuthBearerAuth with a pre-acquired Bearer token.

        Parameters
        ----------
        token : str
            A pre-acquired OAuth 2.0 Bearer token.
        """
        self._token = token

    def auth_flow(
        self,
        request: httpx.Request,
    ):
        """Attach the Bearer token to the request."""
        request.headers["Authorization"] = f"Bearer {self._token}"
        yield request


class KerberosAuth(httpx.Auth):
    """Kerberos/SPNEGO (Negotiate) authentication over pyspnego.

    On a ``401`` carrying ``WWW-Authenticate: Negotiate`` the client generates a
    SPNEGO token for the ``service/hostname`` SPN and retries with an
    ``Authorization: Negotiate`` header. The server's final token is fed back to
    complete mutual authentication.

    Credentials come from the ambient Kerberos cache (the ticket-granting ticket
    obtained via ``kinit``); no username or password is sent. ``hostname`` is
    taken from the request when not overridden, so the same handler serves the
    main, manage and admin ports of one host.

    The token exchange is local CPU work with no network I/O, so one flow serves
    both the sync and async clients.
    """

    NEGOTIATE = "Negotiate"

    def __init__(
        self,
        service: str = "HTTP",
        hostname: str | None = None,
    ):
        """Initialize KerberosAuth.

        Parameters
        ----------
        service : str, default "HTTP"
            The service part of the SPN (``service/hostname``).
        hostname : str | None, default None
            The principal part of the SPN; the request host is used when None.
        """
        self._service = service
        self._hostname = hostname

    def auth_flow(
        self,
        request: httpx.Request,
    ):
        """Negotiate authentication, retrying once with a SPNEGO token."""
        response = yield request
        if not self._needs_negotiation(response):
            return
        context = self._new_context(request.url.host)
        request.headers["Authorization"] = self._initial_header(context)
        response = yield request
        self._verify_mutual_auth(context, response)

    def _needs_negotiation(
        self,
        response: httpx.Response,
    ) -> bool:
        """Whether the server asked for Negotiate authentication."""
        if response.status_code != httpx.codes.UNAUTHORIZED:
            return False
        challenge = response.headers.get("WWW-Authenticate", "")
        return self.NEGOTIATE.lower() in challenge.lower()

    def _new_context(
        self,
        request_host: str,
    ):
        """Create a SPNEGO client context for the target host's SPN."""
        spnego = _import_spnego()
        return spnego.client(
            hostname=self._hostname or request_host,
            service=self._service,
            protocol="kerberos",
        )

    def _initial_header(
        self,
        context,
    ) -> str:
        """Return the first Negotiate header for the SPNEGO exchange."""
        token = context.step()
        return self._negotiate_header(token)

    def _verify_mutual_auth(
        self,
        context,
        response: httpx.Response,
    ) -> None:
        """Feed the server's final token back to confirm its identity.

        A missing token when the context still expects one means the server did
        not prove its identity, so mutual authentication has failed.
        """
        server_token = self._server_token(response)
        if server_token is not None:
            context.step(server_token)
            return
        if not context.complete:
            msg = "Mutual authentication failed: server sent no Negotiate token."
            raise httpx.RequestError(msg, request=response.request)

    def _server_token(
        self,
        response: httpx.Response,
    ) -> bytes | None:
        """Decode the server's Negotiate token, if it sent one."""
        challenge = response.headers.get("WWW-Authenticate", "")
        prefix, _, encoded = challenge.partition(" ")
        if prefix.lower() != self.NEGOTIATE.lower() or not encoded:
            return None
        return base64.b64decode(encoded)

    def _negotiate_header(
        self,
        token: bytes,
    ) -> str:
        """Encode a SPNEGO token into a Negotiate authorization header."""
        return f"{self.NEGOTIATE} {base64.b64encode(token).decode('ascii')}"


class MarkLogicCloudAuth(httpx.Auth):
    """MarkLogic Cloud API key exchanged for a Bearer token, with refresh.

    The API key is posted to ``{base_url}/token`` to obtain a short-lived
    access token, which is then sent as a Bearer token. A 401 triggers a single
    token refresh and retry. Both sync and async request flows are supported.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        token_duration: int = 0,
        verify: _TokenVerify = True,
    ):
        """Initialize MarkLogicCloudAuth.

        Parameters
        ----------
        base_url : str
            The Cloud instance base URL (scheme and host) used to reach /token.
        api_key : str
            The MarkLogic Cloud API key.
        token_duration : int, default 0
            Token lifetime in seconds; 0 uses the server default.
        verify : bool | str | ssl.SSLContext, default True
            Server certificate verification for the token exchange, matching the
            connection's own SSL settings.
        """
        self._token_endpoint = urljoin(base_url, "/token")
        self._api_key = api_key
        self._token_duration = token_duration
        self._verify = verify
        self._token: str | None = None

    def sync_auth_flow(
        self,
        request: httpx.Request,
    ):
        """Attach a Bearer token, fetching/refreshing it synchronously."""
        if self._token is None:
            self._token = self._fetch_token()
        response = yield self._with_token(request)
        if response.status_code == httpx.codes.UNAUTHORIZED:
            self._token = self._fetch_token()
            yield self._with_token(request)

    async def async_auth_flow(
        self,
        request: httpx.Request,
    ):
        """Attach a Bearer token, fetching/refreshing it asynchronously."""
        if self._token is None:
            self._token = await self._afetch_token()
        response = yield self._with_token(request)
        if response.status_code == httpx.codes.UNAUTHORIZED:
            self._token = await self._afetch_token()
            yield self._with_token(request)

    def _with_token(
        self,
        request: httpx.Request,
    ) -> httpx.Request:
        """Set the current Bearer token on the request."""
        request.headers["Authorization"] = f"Bearer {self._token}"
        return request

    def _fetch_token(self) -> str:
        """Exchange the API key for an access token synchronously."""
        response = httpx.post(
            self._token_endpoint,
            verify=self._verify,
            **self._exchange(),
        )
        return self._access_token(response)

    async def _afetch_token(self) -> str:
        """Exchange the API key for an access token asynchronously."""
        async with httpx.AsyncClient(verify=self._verify) as client:
            response = await client.post(self._token_endpoint, **self._exchange())
        return self._access_token(response)

    def _exchange(self) -> dict:
        """Return the token-exchange payload and optional duration param."""
        exchange = {"data": {"grant_type": "apikey", "key": self._api_key}}
        if self._token_duration > 0:
            exchange["params"] = {"duration": self._token_duration}
        return exchange

    @staticmethod
    def _access_token(
        response: httpx.Response,
    ) -> str:
        """Return the access token from a token-exchange response."""
        response.raise_for_status()
        return response.json()["access_token"]

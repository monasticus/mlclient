"""The HTTP Command module.

It exports an implementation for the 'http' command:
    * HttpCommand
        Sends a raw HTTP request to any MarkLogic REST endpoint.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from cleo.io.outputs.output import Type
from httpx import Headers, Response

from mlclient._manager import MLClientManager
from mlclient.cli.connection import get_client
from mlclient.cli.formatting import prettify
from mlclient.clients.http import HttpClient
from mlclient.exceptions import WrongParametersError


class HttpCommand(Command):
    """Sends a raw HTTP request to any REST endpoint.

    Usage:
      http [options] [--] <method> <endpoint> [<params>...]

    Arguments:
      method
            The HTTP method (e.g. get, head, post, put, delete, patch)
      endpoint
            The REST endpoint to call (e.g. /v1/documents)
      params
            Query params (key=value) and headers (key:value)

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name [default: "local"]
      -c, --connection=CONNECTION
            Connection identifier from the environment or TCP port
      -b, --body=BODY
            Request body: a raw string, a file path, or @file-path
      -i, --include
            Include the status line and response headers in the output
      -p, --pretty
            Pretty-print an XML or JSON body
    """

    name: str = "http"
    description: str = "Sends a raw HTTP request to any REST endpoint"
    arguments: list[Argument] = [
        argument(
            "method",
            "The HTTP method (e.g. get, head, post, put, delete, patch)",
        ),
        argument(
            "endpoint",
            "The REST endpoint to call (e.g. /v1/documents)",
        ),
        argument(
            "params",
            "Query params (key=value) and headers (key:value)",
            optional=True,
            multiple=True,
        ),
    ]
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name",
            flag=False,
            default="local",
        ),
        option(
            "connection",
            "c",
            description="Connection identifier from the environment or TCP port",
            flag=False,
        ),
        option(
            "body",
            "b",
            description="Request body: a raw string, a file path, or @file-path",
            flag=False,
        ),
        option(
            "include",
            "i",
            description="Include the status line and response headers in the output",
        ),
        option(
            "pretty",
            "p",
            description="Pretty-print an XML or JSON body",
        ),
    ]

    def handle(self) -> int:
        """Execute the command."""
        method = self.argument("method").upper()
        endpoint = urlsplit(self.argument("endpoint"))
        if endpoint.scheme or endpoint.netloc or endpoint.fragment:
            msg = (
                "Use an endpoint path without a host or fragment; "
                "select its connection with -c."
            )
            raise WrongParametersError(msg)
        params, headers = _parse_params(self.argument("params"))
        query = parse_qs(endpoint.query, keep_blank_values=True)
        for key, values in params.items():
            query.setdefault(key, []).extend(values)
        body = _read_body(self.option("body"))

        mgr = MLClientManager(self.option("environment"))
        with get_client(mgr, self.option("connection")) as ml:
            response = ml.http.request(
                method,
                "/" + endpoint.path.lstrip("/"),
                body,
                params=query or None,
                headers=headers or None,
            )
            output = self._render(method, response)

        self._io.write(output, new_line=True, type=Type.RAW)
        if response.is_error:
            response.raise_for_status()
        return 0

    def _render(
        self,
        method: str,
        response: Response,
    ) -> str:
        """Return the response body, or the full protocol representation.

        A HEAD carries no body, and --include asks for the status line and
        headers, so both fall back to the protocol representation.

        Parameters
        ----------
        method : str
            Uppercase request method
        response : Response
            Received HTTP response

        Returns
        -------
        str
            Decoded body with optional formatting and protocol metadata
        """
        body = response.text
        if self.option("pretty"):
            body = prettify(body, response.headers.get("content-type", ""))
        if method == "HEAD" or self.option("include"):
            return HttpClient.format_http_response(response, body)
        return body


def _parse_params(
    tokens: list[str],
) -> tuple[dict[str, list[str]], Headers]:
    """Split tokens at their first separator, preserving repeated query values.

    Parameters
    ----------
    tokens : list[str]
        key=value query parameters and key:value headers

    Returns
    -------
    tuple[dict[str, list[str]], Headers]
        Query values and case-insensitive headers; the last header value wins

    Raises
    ------
    WrongParametersError
        If a token has no separator or an empty name
    """
    params: dict[str, list[str]] = {}
    headers = Headers()
    for token in tokens:
        eq = token.find("=")
        colon = token.find(":")
        if eq != -1 and (colon == -1 or eq < colon):
            key, value = token.split("=", 1)
            params.setdefault(key, []).append(value)
        elif colon != -1:
            key, value = token.split(":", 1)
            headers[key] = value
        else:
            msg = f"'{token}' is neither a key=value param nor a key:value header!"
            raise WrongParametersError(msg)
        if not key.strip():
            msg = f"Parameter or header name cannot be empty: {token!r}"
            raise WrongParametersError(msg)
    return params, headers


def _read_body(spec: str | None) -> str | bytes | None:
    """Read explicit or existing file paths as bytes; otherwise use literal text.

    Parameters
    ----------
    spec : str | None
        Literal body, existing path, explicit @path, or None for no body

    Returns
    -------
    str | bytes | None
        Literal text or exact file bytes, without newline or encoding conversion

    Raises
    ------
    WrongParametersError
        If a selected file cannot be read
    """
    if spec is None:
        return None
    explicit = spec.startswith("@")
    path = Path(spec[1:] if explicit else spec)
    try:
        is_file = explicit or path.is_file()
    except OSError:
        return spec
    if not is_file:
        return spec
    try:
        return path.read_bytes()
    except OSError as exc:
        msg = f"Cannot read request body from {str(path)!r}: {exc.strerror}"
        raise WrongParametersError(msg) from exc

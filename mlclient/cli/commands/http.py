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
from mlclient.cli.commands._multi_env_common import (
    UnsuccessfulAnswerError,
    selected_environments,
    time_in_environments,
)
from mlclient.cli.connection import get_async_client, get_client
from mlclient.cli.formatting import prettify
from mlclient.clients.http import HttpClient
from mlclient.exceptions import WrongParametersError
from mlclient.models import Mimetypes

_QUERY_PARAM_PREFIXES = (
    "rs:",
    "trans:",
    "perm:",
    "prop:",
    "value:",
    "bind:",
    "get:",
    "put:",
    "post:",
    "delete:",
)


class HttpCommand(Command):
    """Sends a raw HTTP request to any REST endpoint.

    With several environments the request is sent to all of them at once and a
    table with one column per environment shows each output and how long the
    request took. An error response is shown as a failure, and the command
    exits with 1 if any environment failed.

    An error response exits with 1 after printing its body; an empty error body
    is reported as a status line with the URL instead.

    Usage:
      http [options] [--] <method> <endpoint> [<params>...]

    Arguments:
      method
            The HTTP method (e.g. get, head, post, put, delete, patch)
      endpoint
            The REST endpoint to call (e.g. /v1/documents)
      params
            Query params (key=value) and headers (key:value); prefixed MarkLogic
            params (rs:, trans:, perm:, prop:, value:, bind:, get:, put:, post:,
            delete:) with = are query params, e.g. rs:view=versions

    Options:
      -e, --environment=ENVIRONMENT
            The ML Client environment name; repeat it to send the request to several
            environments (multiple values allowed) [default: ["local"]]
      -c, --connection=CONNECTION
            Connection identifier from the environment or TCP port
      -b, --body=BODY
            Request body: a raw string, a file path, or @file-path; a file's
            extension sets the default Content-Type
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
            "Query params (key=value) and headers (key:value); prefixed "
            "MarkLogic params (rs:, trans:, perm:, prop:, value:, bind:, get:, "
            "put:, post:, delete:) with = are query params, e.g. rs:view=versions",
            optional=True,
            multiple=True,
        ),
    ]
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name; repeat it to send the "
            "request to several environments",
            flag=False,
            multiple=True,
            default=["local"],
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
            description="Request body: a raw string, a file path, or @file-path; "
            "a file's extension sets the default Content-Type",
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
        body, body_mimetype = _read_body(self.option("body"))
        if body_mimetype and "content-type" not in headers:
            headers["Content-Type"] = body_mimetype
        request = {
            "method": method,
            "endpoint": "/" + endpoint.path.lstrip("/"),
            "body": body,
            "params": query or None,
            "headers": headers or None,
        }

        environments = selected_environments(self)
        if len(environments) > 1:
            return self._request_in_environments(environments, request)
        mgr = MLClientManager(environments[0])
        with get_client(mgr, self.option("connection")) as ml:
            response = ml.http.request(**request)
            output = self._render(method, response)

        if response.is_error and not output:
            self._io.write_error_line(_status_line(response), type=Type.RAW)
            return 1
        self._io.write(output, new_line=True, type=Type.RAW)
        return 1 if response.is_error else 0

    def _request_in_environments(
        self,
        environments: list[str],
        request: dict,
    ) -> int:
        """Send the request to every environment at once and show the outputs.

        Parameters
        ----------
        environments : list[str]
            Environment names, one table column each, in the given order.
        request : dict
            Keyword arguments for the HTTP client's request method.

        Returns
        -------
        int
            0 when every environment answered with success, 1 when any failed.
        """
        connection = self.option("connection")

        async def send(environment: str) -> Response:
            manager = MLClientManager(environment)
            async with get_async_client(manager, connection) as ml:
                response = await ml.http.request(**request)
            if response.is_error:
                output = self._render(request["method"], response)
                raise UnsuccessfulAnswerError(output or _status_line(response))
            return response

        def describe(response: Response) -> str:
            return self._render(request["method"], response)

        return time_in_environments(self, environments, send, describe)

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
            content_type = response.headers.get("content-type", "").split(";", 1)[0]
            content_type = content_type.strip().lower()
            body = prettify(
                body,
                None if content_type in ("", "text/plain") else content_type,
            )
        if method == "HEAD" or self.option("include"):
            return HttpClient.format_http_response(response, body)
        return body


def _parse_params(
    tokens: list[str],
) -> tuple[dict[str, list[str]], Headers]:
    """Split tokens at their first separator, preserving repeated query values.

    A token with a known MarkLogic parameter prefix (e.g. ``rs:view=versions``)
    and a ``=`` is a query parameter despite the colon before the ``=``.

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
        is_prefixed_param = eq != -1 and token.startswith(_QUERY_PARAM_PREFIXES)
        if is_prefixed_param or (eq != -1 and (colon == -1 or eq < colon)):
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


def _read_body(spec: str | None) -> tuple[str | bytes | None, str | None]:
    """Read explicit or existing file paths as bytes; otherwise use literal text.

    Parameters
    ----------
    spec : str | None
        Literal body, existing path, explicit @path, or None for no body

    Returns
    -------
    tuple[str | bytes | None, str | None]
        Literal text or exact file bytes, without newline or encoding conversion,
        and the MarkLogic mimetype of a file's extension (None for literal text
        or an unknown extension)

    Raises
    ------
    WrongParametersError
        If a selected file cannot be read
    """
    if spec is None:
        return None, None
    explicit = spec.startswith("@")
    path = Path(spec[1:] if explicit else spec)
    try:
        is_file = explicit or path.is_file()
    except OSError:
        return spec, None
    if not is_file:
        return spec, None
    try:
        return path.read_bytes(), Mimetypes.get_mimetype(path.name)
    except OSError as exc:
        msg = f"Cannot read request body from {str(path)!r}: {exc.strerror}"
        raise WrongParametersError(msg) from exc


def _status_line(response: Response) -> str:
    """Describe an error response that has no body to show.

    Parameters
    ----------
    response : Response
        Received HTTP response

    Returns
    -------
    str
        The status code, reason phrase and request URL
    """
    return f"HTTP {response.status_code} {response.reason_phrase} for {response.url}"

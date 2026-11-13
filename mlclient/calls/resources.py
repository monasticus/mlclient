"""The ML Resources Api Calls module.

It exports 4 classes:
    * ResourceGetCall
        A GET request to a resource service extension.
    * ResourcePostCall
        A POST request to a resource service extension.
    * ResourcePutCall
        A PUT request to a resource service extension.
    * ResourceDeleteCall
        A DELETE request to a resource service extension.
"""

from __future__ import annotations

import json
from urllib.parse import quote

from mlclient import _constants as constants
from mlclient import exceptions
from mlclient.calls import _utils as call_utils
from mlclient.calls.base import ApiCall


class _ResourceCall(ApiCall):
    """Endpoint, parameters and body encoding shared by /v1/resources/{name}."""

    _API_VERSION: int = 1

    _ENDPOINT_TEMPLATE: str = "/v{}/resources/{}"

    _DATABASE_PARAM: str = "database"
    _TXID_PARAM: str = "txid"

    def __init__(
        self,
        name: str,
        method: str,
        params: dict | None,
        database: str | None,
        txid: str | None,
        accept: str | None,
        body: str | bytes | dict | list | None = None,
        content_type: str | None = None,
    ):
        """Initialize the shared part of a /v1/resources/{name} call.

        Parameters
        ----------
        name : str
            The name of an installed resource service extension.
        method : str
            The HTTP method.
        params : dict | None
            Extension parameters; see ``extension_params`` in the calls utilities.
        database : str | None
            The content database to perform the operation on.
        txid : str | None
            The multi-statement transaction to service the request in.
        accept : str | None
            The accepted response MIME type.
        body : str | bytes | dict | list | None
            The request body.
        content_type : str | None
            The type of the request body.

        Raises
        ------
        WrongParametersError
            If the name is blank, or the body is unsupported or lacks a type.
        """
        self._validate_name(name)
        body, content_type = self._encode_body(body, content_type)
        super().__init__(
            method=method,
            body=body,
            accept=accept,
            content_type=content_type,
        )
        self._name = name
        self._params = {
            **call_utils.extension_params(params),
            **call_utils.query_params(
                {self._DATABASE_PARAM: database, self._TXID_PARAM: txid},
                None,
            ),
        }

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Resource call.

        Returns
        -------
        str
            A Resource call endpoint with the extension name percent-encoded
        """
        return self._ENDPOINT_TEMPLATE.format(
            self._API_VERSION,
            quote(self._name, safe=""),
        )

    @staticmethod
    def _validate_name(
        name: str | None,
    ):
        """Reject a missing or blank extension name.

        Parameters
        ----------
        name : str | None
            A resource service extension name.

        Raises
        ------
        WrongParametersError
            If the name is None, empty or whitespace only.
        """
        if not name or not name.strip():
            msg = "No resource name provided for /v1/resources/{name}!"
            raise exceptions.WrongParametersError(msg)

    @staticmethod
    def _encode_body(
        body: str | bytes | dict | list | None,
        content_type: str | None,
    ) -> tuple[str | bytes | None, str | None]:
        """Return the body as sent and its Content-Type header value.

        Parameters
        ----------
        body : str | bytes | dict | list | None
            A JSON dict or list, or a str or bytes body of any type.
        content_type : str | None
            The type of the body; a JSON body defaults to application/json.

        Returns
        -------
        tuple[str | bytes | None, str | None]
            A dict or list is serialized to a JSON string; other bodies are
            unchanged.

        Raises
        ------
        WrongParametersError
            If a str or bytes body has no content type, or the body is of
            another type.
        """
        if body is None:
            return None, content_type
        if isinstance(body, (dict, list)):
            return json.dumps(body), content_type or constants.HEADER_JSON
        if not isinstance(body, (str, bytes)):
            msg = (
                "The body must be a dict, list, str or bytes, "
                f"got {type(body).__name__}"
            )
            raise exceptions.WrongParametersError(msg)
        if not content_type:
            msg = "A str or bytes body requires a content_type!"
            raise exceptions.WrongParametersError(msg)
        return body, content_type


class ResourceGetCall(_ResourceCall):
    """A GET request to a resource service extension.

    An ApiCall implementation representing a single GET request
    to the /v1/resources/{name} endpoint.

    Make a GET request to the named resource service extension.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/v1/resources/[name]
    """

    def __init__(
        self,
        name: str,
        params: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        accept: str | None = None,
    ):
        """Initialize ResourceGetCall instance.

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        """
        super().__init__(
            name,
            constants.METHOD_GET,
            params,
            database,
            txid,
            accept,
        )


class ResourcePostCall(_ResourceCall):
    """A POST request to a resource service extension.

    An ApiCall implementation representing a single POST request
    to the /v1/resources/{name} endpoint.

    Applies an extension-specific operation to a resource implemented by
    a resource service extension.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/v1/resources/[name]
    """

    def __init__(
        self,
        name: str,
        params: dict | None = None,
        body: str | bytes | dict | list | None = None,
        content_type: str | None = None,
        database: str | None = None,
        txid: str | None = None,
        accept: str | None = None,
    ):
        """Initialize ResourcePostCall instance.

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        body : str | bytes | dict | list | None
            The request body. A dict or list is sent as JSON; a str or bytes
            body requires a content_type. Without a body the extension still
            runs.
        content_type : str | None
            The type of the request body. The accepted values are service
            dependent. Defaults to application/json for a dict or list body;
            ``multipart/mixed`` with a boundary sends several documents.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        """
        super().__init__(
            name,
            constants.METHOD_POST,
            params,
            database,
            txid,
            accept,
            body,
            content_type,
        )


class ResourcePutCall(_ResourceCall):
    """A PUT request to a resource service extension.

    An ApiCall implementation representing a single PUT request
    to the /v1/resources/{name} endpoint.

    Perform the PUT operation associated with a resource service extension.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/PUT/v1/resources/[name]
    """

    def __init__(
        self,
        name: str,
        params: dict | None = None,
        body: str | bytes | dict | list | None = None,
        content_type: str | None = None,
        database: str | None = None,
        txid: str | None = None,
        accept: str | None = None,
    ):
        """Initialize ResourcePutCall instance.

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        body : str | bytes | dict | list | None
            The request body. A dict or list is sent as JSON; a str or bytes
            body requires a content_type.
        content_type : str | None
            The type of the request body. The accepted values are service
            dependent. Defaults to application/json for a dict or list body;
            ``multipart/mixed`` with a boundary sends several documents.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        """
        super().__init__(
            name,
            constants.METHOD_PUT,
            params,
            database,
            txid,
            accept,
            body,
            content_type,
        )


class ResourceDeleteCall(_ResourceCall):
    """A DELETE request to a resource service extension.

    An ApiCall implementation representing a single DELETE request
    to the /v1/resources/{name} endpoint.

    Send a DELETE request to the named resource service extension.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/v1/resources/[name]
    """

    def __init__(
        self,
        name: str,
        params: dict | None = None,
        database: str | None = None,
        txid: str | None = None,
        accept: str | None = None,
    ):
        """Initialize ResourceDeleteCall instance.

        Parameters
        ----------
        name : str
            The name of a resource service extension installed in the REST API
            instance.
        params : dict | None
            Service-specific parameters, sent with the ``rs:`` prefix (a name
            already starting with ``rs:`` is sent unchanged). A list or tuple
            value is repeated, booleans are sent as ``true`` / ``false`` and
            other values as strings; None is omitted.
        database : str | None
            Perform this operation on the named content database
            instead of the default content database associated with the REST API
            instance. The database can be identified by name or by database id.
        txid : str | None
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        accept : str | None
            The accepted response MIME type, if any. The accepted values depend
            on the service extension implementation.
        """
        super().__init__(
            name,
            constants.METHOD_DELETE,
            params,
            database,
            txid,
            accept,
        )

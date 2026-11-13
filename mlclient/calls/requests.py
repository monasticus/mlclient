"""The ML Requests Api Calls module.

This module provides call classes for request-related REST resources.

It exports 2 classes:
    * RequestsGetCall
        A GET request to get requests summary.
    * RequestGetCall
        A GET request to get request details.
"""

from __future__ import annotations

from typing import ClassVar

from mlclient import _constants as constants
from mlclient import _utils as utils
from mlclient import exceptions
from mlclient.calls import _utils as call_utils
from mlclient.calls.base import ApiCall


class RequestsGetCall(ApiCall):
    """A GET request to get requests summary.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/requests endpoint.

    This resource address returns a summary of the requests in the cluster.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/requests
    """

    _API_VERSION: int = 2

    _ENDPOINT: str = "/manage/v{}/requests"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"
    _GROUP_ID_PARAM: str = "group-id"
    _HOST_ID_PARAM: str = "host-id"
    _SERVER_ID_PARAM: str = "server-id"
    _SECONDS_MIN_PARAM: str = "seconds-min"
    _FULL_REFS_PARAM: str = "fullrefs"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["default", "schema", "describe"]

    def __init__(
        self,
        data_format: str = "xml",
        view: str = "default",
        group_id: str | None = None,
        host_id: str | None = None,
        server_id: str | None = None,
        seconds_min: int | None = None,
        full_refs: bool | None = None,
    ):
        """Initialize RequestsGetCall instance.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be default, schema or describe.
            The schema view requires XML format.
        group_id : str
            Limits the summary to requests in the specified group.
            The group can be identified either by id or name.
        host_id : str
            Limits the summary to requests in the specified host.
            The host can be identified either by id or name.
        server_id : str
            Limits the summary to requests in the specified server.
            The server can be identified either by id or name;
            a name requires group_id.
        seconds_min : int
            Returns only requests that have been executing for at least
            the specified whole number of seconds.
        full_refs : bool
            If set to true, full detail is returned for all relationship references.
            A value of false (the default) indicates to return detail only for first
            references.

        Raises
        ------
        WrongParametersError
            If the format or view is unsupported, or seconds_min is not
            a non-negative integer.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view, seconds_min)

        super().__init__(
            method=constants.METHOD_GET,
            accept=utils.get_accept_header_for_format(data_format),
        )
        if full_refs is not None:
            full_refs = str(full_refs).lower()
        if seconds_min is not None:
            seconds_min = str(seconds_min)
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)
        self.add_param(self._GROUP_ID_PARAM, group_id)
        self.add_param(self._HOST_ID_PARAM, host_id)
        self.add_param(self._SERVER_ID_PARAM, server_id)
        self.add_param(self._SECONDS_MIN_PARAM, seconds_min)
        self.add_param(self._FULL_REFS_PARAM, full_refs)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Requests call.

        Returns
        -------
        str
            A Requests call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)

    @classmethod
    def _validate_params(
        cls,
        data_format: str,
        view: str,
        seconds_min: int | None,
    ):
        """Validate the response format, request-list view and minimum duration.

        Parameters
        ----------
        data_format : str
            Requested response format.
        view : str
            Requested request-list view.
        seconds_min : int | None
            Requested minimum execution time in seconds.

        Raises
        ------
        WrongParametersError
            If the format or view is unsupported, or seconds_min is not
            a non-negative integer (MarkLogic casts it to xs:integer and fails
            with a 500 error otherwise).
        """
        call_utils.validate_supported(
            [data_format],
            cls._SUPPORTED_FORMATS,
            "formats",
            required=True,
        )
        call_utils.validate_supported(
            [view],
            cls._SUPPORTED_VIEWS,
            "views",
            required=True,
        )
        if seconds_min is None:
            return
        is_integer = isinstance(seconds_min, int) and not isinstance(seconds_min, bool)
        if not is_integer or seconds_min < 0:
            msg = "The seconds_min parameter must be a non-negative integer"
            raise exceptions.WrongParametersError(msg)


class RequestGetCall(ApiCall):
    """A GET request to get request details.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/requests/{id|uri} endpoint.

    This resource address returns information on the specified request.
    The request can be identified either by id or URI.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/requests/[id-or-uri]
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/requests/{}"

    _FORMAT_PARAM: str = "format"
    _GROUP_ID_PARAM: str = "group-id"
    _HOST_ID_PARAM: str = "host-id"
    _SERVER_ID_PARAM: str = "server-id"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]

    def __init__(
        self,
        request: str,
        data_format: str = "xml",
        group_id: str | None = None,
        host_id: str | None = None,
        server_id: str | None = None,
    ):
        """Initialize RequestGetCall instance.

        Parameters
        ----------
        request : str
            A request identifier. The request can be identified either by id or URI.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        group_id : str
            Limits the information to the request in the specified group.
            The group can be identified either by id or name.
        host_id : str
            Limits the information to the request in the specified host.
            The host can be identified either by id or name.
        server_id : str
            Limits the information to the request in the specified server.
            The server can be identified either by id or name;
            a name requires group_id.

        Raises
        ------
        WrongParametersError
            If the format is unsupported.
        """
        data_format = data_format if data_format is not None else "xml"
        call_utils.validate_supported(
            [data_format],
            self._SUPPORTED_FORMATS,
            "formats",
            required=True,
        )

        super().__init__(
            method=constants.METHOD_GET,
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._request = request
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._GROUP_ID_PARAM, group_id)
        self.add_param(self._HOST_ID_PARAM, host_id)
        self.add_param(self._SERVER_ID_PARAM, server_id)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Request call.

        Returns
        -------
        str
            A Request call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._request)

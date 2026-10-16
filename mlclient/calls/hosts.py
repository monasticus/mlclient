"""The ML Hosts Api Calls module.

This module provides call classes for host-related REST resources.

It exports 5 classes:
    * HostsGetCall
        A GET request to get hosts summary.
    * HostGetCall
        A GET request to get host details.
    * HostPostCall
        A POST request to restart or shut down a host.
    * HostPropertiesGetCall
        A GET request to get host properties.
    * HostPropertiesPutCall
        A PUT request to modify host properties.
"""

from __future__ import annotations

from typing import ClassVar

from mlclient import _constants as constants
from mlclient import _utils as utils
from mlclient import exceptions
from mlclient.calls import _utils as call_utils
from mlclient.calls.base import ApiCall


class HostsGetCall(ApiCall):
    """A GET request to get hosts summary.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/hosts endpoint.

    This resource address returns data about the hosts in the cluster.
    The data returned depends on the setting of the view request parameter.
    The default view provides a summary of the hosts.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/hosts
    """

    _API_VERSION: int = 2

    _ENDPOINT: str = "/manage/v{}/hosts"

    _FORMAT_PARAM: str = "format"
    _GROUP_ID_PARAM: str = "group-id"
    _VIEW_PARAM: str = "view"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = [
        "default",
        "status",
        "metrics",
        "schema",
        "properties-schema",
        "describe",
    ]

    def __init__(
        self,
        data_format: str = "xml",
        group_id: str | None = None,
        view: str = "default",
    ):
        """Initialize HostsGetCall instance.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        group_id : str
            Specifies to return only the hosts in the specified group.
            The group can be identified either by id or name.
            If not specified, the response includes information about all hosts.
        view : str
            A specific view of the returned data.
            Can be default, status, metrics, schema, properties-schema, or describe.
            The schema view requires XML format.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(
            method="GET",
            accept=utils.get_accept_header_for_format(data_format),
        )
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._GROUP_ID_PARAM, group_id)
        self.add_param(self._VIEW_PARAM, view)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Hosts call.

        Returns
        -------
        str
            A Hosts call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)

    @classmethod
    def _validate_params(
        cls,
        data_format: str,
        view: str,
    ):
        """Validate the response format and host-list view.

        Parameters
        ----------
        data_format : str
            Requested response format.
        view : str
            Requested host-list view.

        Raises
        ------
        WrongParametersError
            If the format or view is unsupported.
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


class HostGetCall(ApiCall):
    """A GET request to get host details.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/hosts/{id|name} endpoint.

    This resource address returns information on a specific host.
    The host can be identified either by id or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/hosts/[id-or-name]
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/hosts/{}"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = [
        "describe",
        "default",
        "config",
        "counts",
        "edit",
        "status",
        "properties-schema",
    ]

    def __init__(
        self,
        host: str,
        data_format: str = "xml",
        view: str = "default",
    ):
        """Initialize HostGetCall instance.

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        view : str
            A specific view of the returned data. Can be properties-schema,
            describe, config, counts, edit, status, or default. The edit view
            redirects (302) to the host page of the Admin Interface.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(
            method=constants.METHOD_GET,
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._host = host
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Host call.

        Returns
        -------
        str
            A Host call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._host)

    @classmethod
    def _validate_params(
        cls,
        data_format: str,
        view: str,
    ):
        """Validate the response format and view.

        Parameters
        ----------
        data_format : str
            Requested response format
        view : str
            Requested view of the host

        Raises
        ------
        WrongParametersError
            If the format or the view is not supported
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


class HostPostCall(ApiCall):
    """A POST request to restart or shut down a host.

    An ApiCall implementation representing a single POST request
    to the /manage/v2/hosts/{id|name} endpoint.

    Initiate a state change on a host: restart or shut it down.
    The host can be identified either by id or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/POST/manage/v2/hosts/[id-or-name]
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/hosts/{}"

    _STATE_PARAM: str = "state"

    _SUPPORTED_STATES: ClassVar[list] = ["shutdown", "restart"]

    def __init__(
        self,
        host: str,
        body: dict,
    ):
        """Initialize HostPostCall instance.

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        body : dict
            Form data with the 'state' property (the type of state change to
            initiate; allowed values: shutdown, restart) and the optional
            'failover' property (true to enable fast failover, false by default).
        """
        self._validate_params(body.get(self._STATE_PARAM))
        super().__init__(
            method=constants.METHOD_POST,
            content_type=constants.HEADER_X_WWW_FORM_URLENCODED,
            body=body,
        )
        self._host = host

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Host call.

        Returns
        -------
        str
            A Host call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._host)

    @classmethod
    def _validate_params(
        cls,
        state: str | None,
    ):
        """Validate the requested state change.

        Parameters
        ----------
        state : str | None
            The state change from the request body

        Raises
        ------
        WrongParametersError
            If the state is missing or not supported
        """
        if state is None:
            msg = "You must include the 'state' parameter within a body!"
            raise exceptions.WrongParametersError(msg)
        call_utils.validate_supported(
            [state],
            cls._SUPPORTED_STATES,
            "states",
            required=True,
        )


class HostPropertiesGetCall(ApiCall):
    """A GET request to get host properties.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/hosts/{id|name}/properties endpoint.

    This resource address returns the current state of modifiable properties
    of the specified host.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/hosts/[id-or-name]/properties
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/hosts/{}/properties"

    _FORMAT_PARAM: str = "format"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]

    def __init__(
        self,
        host: str,
        data_format: str = "xml",
    ):
        """Initialize HostPropertiesGetCall instance.

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be html, json or xml (default).
            This parameter overrides the Accept header if both are present.
        """
        data_format = data_format if data_format is not None else "xml"
        self._validate_params(data_format)

        super().__init__(
            method=constants.METHOD_GET,
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._host = host
        self.add_param(self._FORMAT_PARAM, data_format)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Host Properties call.

        Returns
        -------
        str
            A Host Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._host)

    @classmethod
    def _validate_params(
        cls,
        data_format: str,
    ):
        """Validate the response format.

        Parameters
        ----------
        data_format : str
            Requested response format

        Raises
        ------
        WrongParametersError
            If the format is not xml, json or html
        """
        call_utils.validate_supported(
            [data_format],
            cls._SUPPORTED_FORMATS,
            "formats",
            required=True,
        )


class HostPropertiesPutCall(ApiCall):
    """A PUT request to modify host properties.

    An ApiCall implementation representing a single PUT request
    to the /manage/v2/hosts/{id|name}/properties endpoint.

    Initiate a properties change on the specified host.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/hosts/[id-or-name]/properties
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/hosts/{}/properties"

    def __init__(
        self,
        host: str,
        body: str | dict,
    ):
        """Initialize HostPropertiesPutCall instance.

        Parameters
        ----------
        host : str
            A host identifier. The host can be identified either by ID or name.
        body : str | dict
            Host properties in XML or JSON format.
        """
        body, content_type = call_utils.request_body_with_content_type(
            body,
            "PUT /manage/v2/hosts/{id|name}/properties",
        )
        super().__init__(
            method=constants.METHOD_PUT,
            content_type=content_type,
            body=body,
        )
        self._host = host

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Host Properties call.

        Returns
        -------
        str
            A Host Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._host)

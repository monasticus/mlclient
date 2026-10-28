"""The ML Group Api Calls module.

This module provides call classes for group-related REST resources.

It exports 7 classes:
    * GroupsGetCall
        A GET request to get groups summary.
    * GroupsPostCall
        A POST request to create a new group.
    * GroupGetCall
        A GET request to get group details.
    * GroupPostCall
        A POST request to restart or shut down a group.
    * GroupDeleteCall
        A DELETE request to remove a group from a cluster.
    * GroupPropertiesGetCall
        A GET request to get group properties.
    * GroupPropertiesPutCall
        A PUT request to modify group properties.
"""

from __future__ import annotations

from typing import ClassVar

from mlclient import _constants as constants
from mlclient import _utils as utils
from mlclient.calls import _utils as call_utils
from mlclient.calls.base import ApiCall


class GroupsGetCall(ApiCall):
    """A GET request to get groups summary.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/groups endpoint.

    This resource address returns a summary of the groups in the cluster.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/groups
    """

    _API_VERSION: int = 2

    _ENDPOINT: str = "/manage/v{}/groups"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["describe", "default", "schema"]

    def __init__(
        self,
        data_format: str = "xml",
        view: str = "default",
    ):
        """Initialize GroupsGetCall instance.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        view : str
            A specific view of the returned data. Can be schema, describe,
            or default. The schema view requires XML format.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(
            method=constants.METHOD_GET,
            accept=utils.get_accept_header_for_format(data_format),
        )
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Groups call.

        Returns
        -------
        str
            A Groups call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)

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
            Requested view of the groups

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


class GroupsPostCall(ApiCall):
    """A POST request to create a new group.

    An ApiCall implementation representing a single POST request
    to the /manage/v2/groups endpoint.

    This resource address creates a new group in the cluster.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/groups
    """

    _API_VERSION: int = 2

    _ENDPOINT: str = "/manage/v{}/groups"

    def __init__(
        self,
        body: str | dict,
    ):
        """Initialize GroupsPostCall instance.

        Parameters
        ----------
        body : str | dict
            Group properties in XML or JSON format. The group-name property
            is required.
        """
        body, content_type = call_utils.request_body_with_content_type(
            body,
            "POST /manage/v2/groups",
        )
        super().__init__(
            method=constants.METHOD_POST,
            content_type=content_type,
            body=body,
        )

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Groups call.

        Returns
        -------
        str
            A Groups call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)


class GroupGetCall(ApiCall):
    """A GET request to get group details.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/groups/{id|name} endpoint.

    This resource address returns configuration information for the specified
    group. The group can be identified either by ID or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/groups/[id-or-name]
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/groups/{}"

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
        group: str,
        data_format: str = "xml",
        view: str = "default",
    ):
        """Initialize GroupGetCall instance.

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This value overrides the Accept header if both are present.
        view : str
            A specific view of the returned data. Can be properties-schema,
            describe, config, counts, edit, status, or default. The edit view
            redirects (302) to the group page of the Admin Interface.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(
            method=constants.METHOD_GET,
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._group = group
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Group call.

        Returns
        -------
        str
            A Group call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._group)

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
            Requested view of the group

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


class GroupPostCall(ApiCall):
    """A POST request to restart or shut down a group.

    An ApiCall implementation representing a single POST request
    to the /manage/v2/groups/{id|name} endpoint.

    This resource address can be used to restart or shutdown a group in the
    cluster. The group can be identified either by ID or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/POST/manage/v2/groups/[id-or-name]
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/groups/{}"

    def __init__(
        self,
        group: str,
        body: str | dict,
    ):
        """Initialize GroupPostCall instance.

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        body : str | dict
            The operation in XML or JSON format: {"operation": "restart-group"}
            or {"operation": "shutdown-group"}.
        """
        body, content_type = call_utils.request_body_with_content_type(
            body,
            "POST /manage/v2/groups/{id|name}",
        )
        super().__init__(
            method=constants.METHOD_POST,
            content_type=content_type,
            body=body,
        )
        self._group = group

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Group call.

        Returns
        -------
        str
            A Group call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._group)


class GroupDeleteCall(ApiCall):
    """A DELETE request to remove a group from a cluster.

    An ApiCall implementation representing a single DELETE request
    to the /manage/v2/groups/{id|name} endpoint.

    This resource address deletes the specified group from the cluster.
    The group can be identified either by ID or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/DELETE/manage/v2/groups/[id-or-name]
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/groups/{}"

    def __init__(
        self,
        group: str,
    ):
        """Initialize GroupDeleteCall instance.

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        """
        super().__init__(method=constants.METHOD_DELETE)
        self._group = group

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Group call.

        Returns
        -------
        str
            A Group call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._group)


class GroupPropertiesGetCall(ApiCall):
    """A GET request to get group properties.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/groups/{id|name}/properties endpoint.

    This resource address returns the current state of modifiable properties
    of the specified group.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/groups/[id-or-name]/properties
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/groups/{}/properties"

    _FORMAT_PARAM: str = "format"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]

    def __init__(
        self,
        group: str,
        data_format: str = "xml",
    ):
        """Initialize GroupPropertiesGetCall instance.

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be html, json or xml (default).
            This parameter overrides the Accept header if both are present.
        """
        data_format = data_format if data_format is not None else "xml"
        self._validate_params(data_format)

        super().__init__(
            method="GET",
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._group = group
        self.add_param(self._FORMAT_PARAM, data_format)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Group Properties call.

        Returns
        -------
        str
            A Group Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._group)

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


class GroupPropertiesPutCall(ApiCall):
    """A PUT request to modify group properties.

    An ApiCall implementation representing a single PUT request
    to the /manage/v2/groups/{id|name}/properties endpoint.

    Initiate a properties change on the specified group.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/groups/[id-or-name]/properties
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/groups/{}/properties"

    def __init__(
        self,
        group: str,
        body: str | dict,
    ):
        """Initialize GroupPropertiesPutCall instance.

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        body : str | dict
            Group properties in XML or JSON format.
        """
        body, content_type = call_utils.request_body_with_content_type(
            body,
            "PUT /manage/v2/groups/{id|name}/properties",
        )
        super().__init__(method="PUT", content_type=content_type, body=body)
        self._group = group

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Group Properties call.

        Returns
        -------
        str
            A Group Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._group)

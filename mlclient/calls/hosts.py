"""The ML Hosts Api Calls module.

This module provides call classes for host-related REST resources.

It exports 1 class:
    * HostsGetCall
        A GET request to get hosts summary.
"""

from __future__ import annotations

from typing import ClassVar

from mlclient import _utils as utils
from mlclient import exceptions
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
            Can be status, metrics, properties-schema, describe, or default.
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
        if data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)
        if view not in cls._SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(cls._SUPPORTED_VIEWS)
            msg = f"The supported views are: {joined_supported_views}"
            raise exceptions.WrongParametersError(msg)

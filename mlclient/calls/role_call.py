"""The ML Role Resource Calls module.

It exports 2 classes:
    * RoleGetCall
        A GET request to get a role details.
    * RoleDeleteCall
        A DELETE request to remove a role.
"""
from __future__ import annotations

from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class RoleGetCall(ResourceCall):
    """A GET request to get a role details.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/roles/{id|name} REST Resource.

    This resource address returns the configuration for the specified role.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/roles/[id-or-name]
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/roles/{}"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["describe", "default"]

    def __init__(
            self,
            role: str,
            data_format: str = "xml",
            view: str = "default",
    ):
        """Initialize RoleGetCall instance.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter is not meaningful with view=edit.
        view : str
            A specific view of the returned data. Can be: describe, or default.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self._role = role
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Role call.

        Returns
        -------
        str
            A Role call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._role)

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


class RoleDeleteCall(ResourceCall):
    """A DELETE request to remove a role.

    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/roles/{id|name} REST Resource.

    This resource address deletes the named role from the named security database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/roles/[id-or-name]
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/roles/{}"

    def __init__(
            self,
            role: str,
    ):
        """Initialize RoleDeleteCall instance.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        """
        super().__init__(method=constants.METHOD_DELETE)
        self._role = role

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Role call.

        Returns
        -------
        str
            A Role call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._role)

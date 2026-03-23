"""The ML Role Api Calls module.

This module provides call classes for role-related REST resources.

It exports 6 classes:
    * RolesGetCall
        A GET request to get roles summary.
    * RolesPostCall
        A POST request to create a new role.
    * RoleGetCall
        A GET request to get a role details.
    * RoleDeleteCall
        A DELETE request to remove a role.
    * RolePropertiesGetCall
        A GET request to get role properties.
    * RolePropertiesPutCall
        A PUT request to modify role properties.
"""

from __future__ import annotations

import json
import re
from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls.api_call import ApiCall


class RolesGetCall(ApiCall):
    """A GET request to get roles summary.

    A ApiCall implementation representing a single GET request
    to the /manage/v2/roles endpoint.

    This resource address returns a summary of the roles in the security database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/roles
    """

    _API_VERSION: int = 2

    _ENDPOINT: str = "/manage/v{}/roles"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["describe", "default"]

    def __init__(
        self,
        data_format: str = "xml",
        view: str = "default",
    ):
        """Initialize RolesGetCall instance.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(
            method="GET",
            accept=utils.get_accept_header_for_format(data_format),
        )
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Roles call.

        Returns
        -------
        str
            A Roles call endpoint
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


class RolesPostCall(ApiCall):
    """A POST request to create a new role.

    A ApiCall implementation representing a single POST request
    to the /manage/v2/roles endpoint.

    This resource address creates a new role in the security database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/roles
    """

    _API_VERSION: int = 2

    _ENDPOINT: str = "/manage/v{}/roles"

    def __init__(
        self,
        body: str | dict,
    ):
        """Initialize RolesPostCall instance.

        Parameters
        ----------
        body : str | dict
            A role properties in XML or JSON format.
        """
        self._validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="POST", content_type=content_type, body=body)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Roles call.

        Returns
        -------
        str
            A Roles call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)

    @classmethod
    def _validate_params(
        cls,
        body: str | dict,
    ):
        if body is None or (isinstance(body, str) and re.search("^\\s*$", body)):
            msg = "No request body provided for POST /manage/v2/roles!"
            raise exceptions.WrongParametersError(msg)


class RoleGetCall(ApiCall):
    """A GET request to get a role details.

    A ApiCall implementation representing a single GET request
    to the /manage/v2/roles/{id|name} endpoint.

    This resource address returns the configuration for the specified role.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/roles/[id-or-name]
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/roles/{}"

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

        super().__init__(
            method="GET",
            accept=utils.get_accept_header_for_format(data_format),
        )
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
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._role)

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


class RoleDeleteCall(ApiCall):
    """A DELETE request to remove a role.

    A ApiCall implementation representing a single DELETE request
    to the /manage/v2/roles/{id|name} endpoint.

    This resource address deletes the named role from the named security database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/roles/[id-or-name]
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/roles/{}"

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
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._role)


class RolePropertiesGetCall(ApiCall):
    """A GET request to get role properties.

    A ApiCall implementation representing a single GET request
    to the /manage/v2/roles/{id|name}/properties endpoint.

    This resource address returns the properties of the specified role.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/roles/[id-or-name]/properties
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/roles/{}/properties"

    _FORMAT_PARAM: str = "format"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]

    def __init__(
        self,
        role: str,
        data_format: str = "xml",
    ):
        """Initialize RolePropertiesGetCall instance.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        """
        data_format = data_format if data_format is not None else "xml"
        self._validate_params(data_format)

        super().__init__(
            method="GET",
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._role = role
        self.add_param(self._FORMAT_PARAM, data_format)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Role Properties call.

        Returns
        -------
        str
            A Role Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._role)

    @classmethod
    def _validate_params(
        cls,
        data_format: str,
    ):
        if data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)


class RolePropertiesPutCall(ApiCall):
    """A PUT request to modify role properties.

    A ApiCall implementation representing a single PUT request
    to the /manage/v2/roles/{id|name}/properties endpoint.

    This resource address can be used to update the properties for the specified role.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/roles/[id-or-name]/properties
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/roles/{}/properties"

    def __init__(
        self,
        role: str,
        body: str | dict,
    ):
        """Initialize RolePropertiesPutCall instance.

        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        body : str | dict
            A role properties in XML or JSON format.
        """
        self._validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="PUT", content_type=content_type, body=body)
        self._role = role

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Role Properties call.

        Returns
        -------
        str
            A Role Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._role)

    @classmethod
    def _validate_params(
        cls,
        body: str | dict,
    ):
        if body is None or (isinstance(body, str) and re.search("^\\s*$", body)):
            msg = (
                "No request body provided for "
                "PUT /manage/v2/roles/{id|name}/properties!"
            )
            raise exceptions.WrongParametersError(msg)

"""The ML User Api Calls module.

This module provides call classes for user-related REST resources.

It exports 6 classes:
    * UsersGetCall
        A GET request to get users summary.
    * UsersPostCall
        A POST request to create a new user.
    * UserGetCall
        A GET request to get user details.
    * UserDeleteCall
        A DELETE request to remove a user.
    * UserPropertiesGetCall
        A GET request to get user properties.
    * UserPropertiesPutCall
        A PUT request to modify user properties.
"""

from __future__ import annotations

import json
import re
from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls.api_call import ApiCall


class UsersGetCall(ApiCall):
    """A GET request to get users summary.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/users endpoint.

    This resource address returns a summary of the users in the cluster.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/users
    """

    _API_VERSION: int = 2

    _ENDPOINT: str = "/manage/v{}/users"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["describe", "default"]

    def __init__(
        self,
        data_format: str = "xml",
        view: str = "default",
    ):
        """Initialize UsersGetCall instance.

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
        """An endpoint for the Users call.

        Returns
        -------
        str
            A Users call endpoint
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


class UsersPostCall(ApiCall):
    """A POST request to create a new user.

    An ApiCall implementation representing a single POST request
    to the /manage/v2/users endpoint.

    This resource address creates a new user in the security database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/users
    """

    _API_VERSION: int = 2

    _ENDPOINT: str = "/manage/v{}/users"

    def __init__(
        self,
        body: str | dict,
    ):
        """Initialize UsersPostCall instance.

        Parameters
        ----------
        body : str | dict
            A user properties in XML or JSON format.
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
        """An endpoint for the Users call.

        Returns
        -------
        str
            A Users call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)

    @classmethod
    def _validate_params(
        cls,
        body: str | dict,
    ):
        if body is None or (isinstance(body, str) and re.search("^\\s*$", body)):
            msg = "No request body provided for POST /manage/v2/users!"
            raise exceptions.WrongParametersError(msg)


class UserGetCall(ApiCall):
    """A GET request to get user details.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/users/{id|name} endpoint.

    This resource address returns the configuration for the specified user.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/users/[id-or-name]
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/users/{}"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["describe", "default"]

    def __init__(
        self,
        user: str,
        data_format: str = "xml",
        view: str = "default",
    ):
        """Initialize UserGetCall instance.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
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
        self._user = user
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the User call.

        Returns
        -------
        str
            A User call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._user)

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


class UserDeleteCall(ApiCall):
    """A DELETE request to remove a user.

    An ApiCall implementation representing a single DELETE request
    to the /manage/v2/users/{id|name} endpoint.

    This resource address deletes the named user from the named security database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/users/[id-or-name]
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/users/{}"

    def __init__(
        self,
        user: str,
    ):
        """Initialize UserDeleteCall instance.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        """
        super().__init__(method=constants.METHOD_DELETE)
        self._user = user

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the User call.

        Returns
        -------
        str
            A User call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._user)


class UserPropertiesGetCall(ApiCall):
    """A GET request to get user properties.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/users/{id|name}/properties endpoint.

    This resource address returns the properties of the specified user.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/users/[id-or-name]/properties
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/users/{}/properties"

    _FORMAT_PARAM: str = "format"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]

    def __init__(
        self,
        user: str,
        data_format: str = "xml",
    ):
        """Initialize UserPropertiesGetCall instance.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
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
        self._user = user
        self.add_param(self._FORMAT_PARAM, data_format)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the User Properties call.

        Returns
        -------
        str
            A User Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._user)

    @classmethod
    def _validate_params(
        cls,
        data_format: str,
    ):
        if data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)


class UserPropertiesPutCall(ApiCall):
    """A PUT request to modify user properties.

    An ApiCall implementation representing a single PUT request
    to the /manage/v2/users/{id|name}/properties endpoint.

    This resource address can be used to update the properties for the specified user.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/users/[id-or-name]/properties
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/users/{}/properties"

    def __init__(
        self,
        user: str,
        body: str | dict,
    ):
        """Initialize UserPropertiesPutCall instance.

        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        body : str | dict
            A user properties in XML or JSON format.
        """
        self._validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="PUT", content_type=content_type, body=body)
        self._user = user

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the User Properties call.

        Returns
        -------
        str
            A User Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._user)

    @classmethod
    def _validate_params(
        cls,
        body: str | dict,
    ):
        if body is None or (isinstance(body, str) and re.search("^\\s*$", body)):
            msg = (
                "No request body provided for "
                "PUT /manage/v2/users/{id|name}/properties!"
            )
            raise exceptions.WrongParametersError(msg)

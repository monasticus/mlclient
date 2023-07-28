
from __future__ import annotations

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class RoleGetCall(ResourceCall):
    """A GET request to get a role details.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/roles/{id|name} REST Resource.

    This resource address returns the configuration for the specified role.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/roles/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/roles/{}"

    __FORMAT_PARAM = "format"
    __VIEW_PARAM = "view"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default"]

    def __init__(
            self,
            role: str,
            data_format: str = "xml",
            view: str = "default"
    ):
        """
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
        RoleGetCall.__validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__role = role
        self.add_param(RoleGetCall.__FORMAT_PARAM, data_format)
        self.add_param(RoleGetCall.__VIEW_PARAM, view)

    def endpoint(
            self
    ):
        """Return an endpoint for the Role call.

        Returns
        -------
        str
            A Role call endpoint
        """
        return RoleGetCall.__ENDPOINT_TEMPLATE.format(self.__role)

    @classmethod
    def __validate_params(
            cls,
            data_format: str,
            view: str
    ):
        if data_format not in cls.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls.__SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)
        if view not in cls.__SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(cls.__SUPPORTED_VIEWS)
            msg = f"The supported views are: {joined_supported_views}"
            raise exceptions.WrongParametersError(msg)


class RoleDeleteCall(ResourceCall):
    """A DELETE request to remove a role.

    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/roles/{id|name} REST Resource.

    This resource address deletes the named role from the named security database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/roles/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/roles/{}"

    def __init__(
            self,
            role: str
    ):
        """
        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        """
        super().__init__(method=constants.METHOD_DELETE)
        self.__role = role

    def endpoint(
            self
    ):
        """Return an endpoint for the Role call.

        Returns
        -------
        str
            A Role call endpoint
        """
        return RoleDeleteCall.__ENDPOINT_TEMPLATE.format(self.__role)

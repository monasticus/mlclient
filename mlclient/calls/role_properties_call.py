from __future__ import annotations

import json
import re
from typing import Union

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class RolePropertiesGetCall(ResourceCall):
    """A GET request to get role properties.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/roles/{id|name}/properties REST Resource.

    This resource address returns the properties of the specified role.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/roles/[id-or-name]/properties

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/roles/{}/properties"

    __FORMAT_PARAM = "format"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]

    def __init__(
            self,
            role: str,
            data_format: str = "xml"
    ):
        """
        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        """
        data_format = data_format if data_format is not None else "xml"
        RolePropertiesGetCall.__validate_params(data_format)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__role = role
        self.add_param(RolePropertiesGetCall.__FORMAT_PARAM, data_format)

    def endpoint(
            self
    ):
        """Return an endpoint for the Role Properties call.

        Returns
        -------
        str
            A Role Properties call endpoint
        """
        return RolePropertiesGetCall.__ENDPOINT_TEMPLATE.format(self.__role)

    @classmethod
    def __validate_params(
            cls,
            data_format: str
    ):
        if data_format not in cls.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls.__SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)


class RolePropertiesPutCall(ResourceCall):
    """A PUT request to modify role properties.

    A ResourceCall implementation representing a single PUT request
    to the /manage/v2/roles/{id|name}/properties REST Resource.

    This resource address can be used to update the properties for the specified role.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/roles/[id-or-name]/properties

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/roles/{}/properties"

    def __init__(
            self,
            role: str,
            body: Union[str, dict]
    ):
        """
        Parameters
        ----------
        role : str
            A role identifier. The role can be identified either by ID or name.
        body : Union[str, dict]
            A role properties in XML or JSON format.
        """
        RolePropertiesPutCall.__validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="PUT",
                         content_type=content_type,
                         body=body)
        self.__role = role

    def endpoint(
            self
    ):
        """Return an endpoint for the Role Properties call.

        Returns
        -------
        str
            A Role Properties call endpoint
        """
        return RolePropertiesPutCall.__ENDPOINT_TEMPLATE.format(self.__role)

    @classmethod
    def __validate_params(
            cls,
            body: Union[str, dict]
    ):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            msg = ("No request body provided for "
                   "PUT /manage/v2/roles/{id|name}/properties!")
            raise exceptions.WrongParametersError(msg)

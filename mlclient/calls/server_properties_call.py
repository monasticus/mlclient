"""The ML Server Properties Resource Calls module.

It exports 2 classes:
    * ServerPropertiesGetCall
        A GET request to get app server properties.
    * ServerPropertiesPutCall
        A PUT request to modify app server properties.
"""
from __future__ import annotations

import json
import re
from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class ServerPropertiesGetCall(ResourceCall):
    """A GET request to get app server properties.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/servers/{id|name}/properties REST Resource.

    This resource address returns the current state of modifiable properties
    of the specified App Server.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/servers/[id-or-name]/properties
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/servers/{}/properties"

    _GROUP_ID_PARAM: str = "group-id"
    _FORMAT_PARAM: str = "format"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]

    def __init__(
            self,
            server: str,
            group_id: str,
            data_format: str = "xml",
    ):
        """Initialize ServerPropertiesGetCall instance.

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs.
            This parameter is required.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        """
        data_format = data_format if data_format is not None else "xml"
        self._validate_params(data_format)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self._server = server
        self.add_param(self._GROUP_ID_PARAM, group_id)
        self.add_param(self._FORMAT_PARAM, data_format)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Server Properties call.

        Returns
        -------
        str
            A Server Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._server)

    @classmethod
    def _validate_params(
            cls,
            data_format: str,
    ):
        if data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)


class ServerPropertiesPutCall(ResourceCall):
    """A PUT request to modify app server properties.

    A ResourceCall implementation representing a single PUT request
    to the /manage/v2/servers/{id|name}/properties REST Resource.

    Initiate a properties change on the specified App Server.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/servers/[id-or-name]/properties
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/servers/{}/properties"

    _GROUP_ID_PARAM: str = "group-id"

    def __init__(
            self,
            server: str,
            group_id: str,
            body: str | dict,
    ):
        """Initialize ServerPropertiesPutCall instance.

        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs.
            This parameter is required.
        body : str | dict
            A database properties in XML or JSON format.
        """
        self._validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="PUT",
                         content_type=content_type,
                         body=body)
        self._server = server
        self.add_param(self._GROUP_ID_PARAM, group_id)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Server Properties call.

        Returns
        -------
        str
            A Server Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._server)

    @classmethod
    def _validate_params(
            cls,
            body: str | dict,
    ):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            msg = ("No request body provided for "
                   "PUT /manage/v2/servers/{id|name}/properties!")
            raise exceptions.WrongParametersError(msg)

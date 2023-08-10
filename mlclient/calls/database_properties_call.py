"""The ML Database Properties Resource Calls module.

It exports 2 classes:
    * DatabasePropertiesGetCall
        A GET request to get a database properties.
    * DatabasePropertiesPutCall
        A PUT request to modify database properties.
"""
from __future__ import annotations

import json
import re
from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class DatabasePropertiesGetCall(ResourceCall):
    """A GET request to get a database properties.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/databases/{id|name}/properties REST Resource.

    This resource address returns the modifiable properties of the named database.
    The database can be identified either by ID or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/databases/[id-or-name]/properties
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/databases/{}/properties"

    _FORMAT_PARAM: str = "format"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]

    def __init__(
            self,
            database: str,
            data_format: str = "xml",
    ):
        """Initialize DatabasePropertiesGetCall instance.

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        """
        data_format = data_format if data_format is not None else "xml"
        self._validate_params(data_format)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self._database = database
        self.add_param(self._FORMAT_PARAM, data_format)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Database Properties call.

        Returns
        -------
        str
            A Database Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._database)

    @classmethod
    def _validate_params(
            cls,
            data_format: str,
    ):
        if data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)


class DatabasePropertiesPutCall(ResourceCall):
    """A PUT request to modify database properties.

    A ResourceCall implementation representing a single PUT request
    to the /manage/v2/databases/{id|name}/properties REST Resource.

    This resource address modifies the properties of the named database.
    The list of modifiable properties can be returned by the GET version
    of this endpoint. The database can be identified either by id or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/databases/[id-or-name]/properties
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/databases/{}/properties"

    def __init__(
            self,
            database: str,
            body: str | dict,
    ):
        """Initialize DatabasePropertiesPutCall instance.

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : str | dict
            A database properties in XML or JSON format.
        """
        self.__validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="PUT",
                         content_type=content_type,
                         body=body)
        self._database = database

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Database Properties call.

        Returns
        -------
        str
            A Database Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._database)

    @classmethod
    def __validate_params(
            cls,
            body: str | dict,
    ):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            msg = ("No request body provided for "
                   "PUT /manage/v2/databases/{id|name}/properties!")
            raise exceptions.WrongParametersError(msg)

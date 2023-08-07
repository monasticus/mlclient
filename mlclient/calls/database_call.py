"""The ML Database Resource Calls module.

It exports 3 classes:
    * DatabaseGetCall
        A GET request to get database details.
    * DatabasePostCall
        A POST request to manage a database.
    * DatabaseDeleteCall
        A DELETE request to remove a database from a cluster.
"""
from __future__ import annotations

import json
import re
from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class DatabaseGetCall(ResourceCall):
    """A GET request to get database details.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/databases/{id|name} REST Resource.

    This resource address returns information on the specified database.
    The database can be identified either by ID or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/databases/[id-or-name]
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/databases/{}"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["describe", "default", "config", "counts",
                                        "edit", "package", "status", "forest-storage",
                                        "properties-schema"]

    def __init__(
            self,
            database: str,
            data_format: str = "xml",
            view: str = "default",
    ):
        """Initialize DatabaseGetCall instance.

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter is not meaningful with view=edit.
        view : str
            A specific view of the returned data.
            Can be: properties-schema, package, describe, config, counts, edit, status,
            forest-storage, or default.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__database = database
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Database call.

        Returns
        -------
        str
            A Database call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self.__database)

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


class DatabasePostCall(ResourceCall):
    """A POST request to manage a database.

    A ResourceCall implementation representing a single POST request
    to the /manage/v2/databases/{id|name} REST Resource.

    This resource address can be used to clear the contents of the named database
    and to perform various configuration operations on the database.
    The database can be identified either by id or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/POST/manage/v2/databases/[id-or-name]
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/databases/{}"

    def __init__(
            self,
            database: str,
            body: str | dict,
    ):
        """Initialize DatabasePostCall instance.

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : str | dict
            A database properties in XML or JSON format.
        """
        self._validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="POST",
                         content_type=content_type,
                         body=body)
        self.__database = database

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Database call.

        Returns
        -------
        str
            A Database call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self.__database)

    @classmethod
    def _validate_params(
            cls,
            body: str | dict,
    ):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            msg = "No request body provided for POST /manage/v2/databases/{id|name}!"
            raise exceptions.WrongParametersError(msg)


class DatabaseDeleteCall(ResourceCall):
    """A DELETE request to remove a database from a cluster.

    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/databases/{id|name} REST Resource.

    This resource address deletes the named database from the cluster.
    The database can be identified either by id or name.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/databases/[id-or-name]
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/databases/{}"

    _FOREST_DELETE_PARAM: str = "forest-delete"

    _SUPPORTED_FOREST_DELETE_OPTS: ClassVar[list] = ["configuration", "data"]

    def __init__(
            self,
            database: str,
            forest_delete: str | None = None,
    ):
        """Initialize DatabaseDeleteCall instance.

        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        forest_delete : str
            Specifies to delete the forests attached to the database.
            If unspecified, the forests will not be affected.
            If "configuration" is specified, the forest configuration will be removed
            but public forest data will remain.
            If "data" is specified, the forest configuration and data will be removed.
        """
        self._validate_params(forest_delete)
        super().__init__(method=constants.METHOD_DELETE)
        self.add_param(self._FOREST_DELETE_PARAM, forest_delete)
        self._database = database

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Database call.

        Returns
        -------
        str
            A Database call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._database)

    @classmethod
    def _validate_params(
            cls,
            forest_delete: str,
    ):
        if forest_delete and forest_delete not in cls._SUPPORTED_FOREST_DELETE_OPTS:
            joined_supported_opts = ", ".join(cls._SUPPORTED_FOREST_DELETE_OPTS)
            msg = f"The supported forest_delete options are: {joined_supported_opts}"
            raise exceptions.WrongParametersError(msg)

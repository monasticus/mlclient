"""The ML Documents Resource Calls module.

It exports 1 class:
    * DocumentsGetCall
        A GET request to retrieve documents' content or metadata.
"""
from __future__ import annotations

from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class DocumentsGetCall(ResourceCall):
    """A GET request to retrieve documents' content or metadata.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/documents REST Resource.

    Retrieve document content and/or metadata from the database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/v1/documents
    """

    _ENDPOINT: str = "/v1/documents"

    _URI_PARAM: str = "uri"
    _DATABASE_PARAM: str = "database"
    _CATEGORY_PARAM: str = "category"
    _FORMAT_PARAM: str = "format"
    _TIMESTAMP_PARAM: str = "timestamp"
    _TRANSFORM_PARAM: str = "transform"
    _TXID_PARAM: str = "txid"
    _TRANS_PARAM_PREFIX: str = "trans:"

    _SUPPORTED_FORMATS: ClassVar[list] = ["binary", "json", "text", "xml"]
    _SUPPORTED_METADATA_FORMATS: ClassVar[list] = ["json", "xml"]
    _SUPPORTED_CATEGORIES: ClassVar[list] = ["content", "metadata", "metadata-values",
                                             "collections", "permissions", "properties",
                                             "quality"]

    def __init__(
            self,
            uri: str | list,
            database: str | None = None,
            category: str | None = None,
            data_format: str | None = None,
            timestamp: str | None = None,
            transform: str | None = None,
            transform_params: dict | None = None,
            txid: str | None = None,
    ):
        """Initialize DocumentsGetCall instance.

        Parameters
        ----------
        uri : str | list
            One or more URIs for documents in the database.
            If you specify multiple URIs, the Accept header must be multipart/mixed.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str
            The category of data to fetch about the requested document.
            Category can be specified multiple times to retrieve any combination
            of content and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.
        data_format : str
            The expected format of metadata returned in the response.
            Accepted values: xml or json.
            This parameter does not affect document content.
            For metadata, this parameter overrides the MIME type in the Accept header,
            except when the Accept header is multipart/mixed.
        timestamp : str
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request. Use this parameter to fetch documents based on the contents
            of the database at a fixed point-in-time.
        transform : str
            Names a content transformation previously installed via
            the /config/transforms service. The service applies the transformation
            to all documents prior to constructing the response.
        transform_params : str
            A transform parameter names and values. For example, { "myparam": 1 }.
            Transform parameters are passed to the transform named in the transform
            parameter.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        """
        self._validate_params(category, data_format)

        super().__init__(method="GET")
        accept_header = self._get_accept_header(uri, category, data_format)
        self.add_header(constants.HEADER_NAME_ACCEPT, accept_header)
        self.add_param(self._URI_PARAM, uri)
        self.add_param(self._DATABASE_PARAM, database)
        self.add_param(self._CATEGORY_PARAM, category)
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._TIMESTAMP_PARAM, timestamp)
        self.add_param(self._TRANSFORM_PARAM, transform)
        self.add_param(self._TXID_PARAM, txid)
        if transform_params:
            for trans_param_name, value in transform_params.items():
                param = self._TRANS_PARAM_PREFIX + trans_param_name
                self.add_param(param, value)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Documents call.

        Returns
        -------
        str
            A Documents call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
            cls,
            category: str,
            data_format: str,
    ):
        if category and category not in cls._SUPPORTED_CATEGORIES:
            joined_supported_categories = ", ".join(cls._SUPPORTED_CATEGORIES)
            msg = f"The supported categories are: {joined_supported_categories}"
            raise exceptions.WrongParametersError(msg)
        if data_format and data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)
        if (category and category != "content" and
                data_format and data_format not in cls._SUPPORTED_METADATA_FORMATS):
            joined_supported_formats = ", ".join(cls._SUPPORTED_METADATA_FORMATS)
            msg = f"The supported metadata formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)

    @staticmethod
    def _get_accept_header(
            uri: str | list,
            category: str,
            data_format: str,
    ):
        if not isinstance(uri, str) and len(uri) > 1:
            return constants.HEADER_MULTIPART_MIXED
        if data_format is not None and category is not None and category != "content":
            return utils.get_accept_header_for_format(data_format)
        return None

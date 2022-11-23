from typing import Union

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class DocumentsGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request to the /manage/v2/documents REST Resource

    Retrieve document content and/or metadata from the database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/v1/documents

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    ENDPOINT = "/v1/documents"

    __URI_PARAM = "uri"
    __DATABASE_PARAM = "database"
    __CATEGORY_PARAM = "category"
    __FORMAT_PARAM = "format"
    __TIMESTAMP_PARAM = "timestamp"
    __TRANSFORM_PARAM = "transform"
    __TXID_PARAM = "txid"
    __TRANS_PARAM_PREFIX = "trans:"

    __SUPPORTED_FORMATS = ["binary", "json", "text", "xml"]
    __SUPPORTED_METADATA_FORMATS = ["json", "xml"]
    __SUPPORTED_CATEGORIES = ["content", "metadata", "metadata-values", "collections", "permissions", "properties",
                              "quality"]

    def __init__(self, uri: Union[str, list], database: str = None, category: str = None, data_format: str = None,
                 timestamp: str = None, transform: str = None, transform_params: dict = None, txid: str = None):
        """
        Parameters
        ----------
        uri : Union[str, list]
            One or more URIs for documents in the database.
            If you specify multiple URIs, the Accept header must be multipart/mixed.
        database : str
            Perform this operation on the named content database instead of the default content database
            associated with the REST API instance. Using an alternative database requires the "eval-in" privilege.
        category : str
            The category of data to fetch about the requested document.
            Category can be specified multiple times to retrieve any combination of content and metadata.
            Valid categories: content (default), metadata, metadata-values, collections, permissions,
            properties, and quality. Use metadata to request all categories except content.
        data_format : str
            The expected format of metadata returned in the response. Accepted values: xml or json.
            This parameter does not affect document content.
            For metadata, this parameter overrides the MIME type in the Accept header,
            except when the Accept header is multipart/mixed.
        timestamp : str
            A timestamp returned in the ML-Effective-Timestamp header of a previous request.
            Use this parameter to fetch documents based on the contents of the database at a fixed point-in-time.
        transform : str
            Names a content transformation previously installed via the /config/transforms service.
            The service applies the transformation to all documents prior to constructing the response.
        transform_params : str
            A transform parameter names and values. For example, { "myparam": 1 }.
            Transform parameters are passed to the transform named in the transform parameter.
        txid : str
            The transaction identifier of the multi-statement transaction in which to service this request.
            Use the /transactions service to create and manage multi-statement transactions.
        """

        DocumentsGetCall.__validate_params(category, data_format)

        super().__init__(method="GET")
        self.add_header(constants.HEADER_NAME_ACCEPT, self.__get_accept_header(uri, category, data_format))
        self.add_param(DocumentsGetCall.__URI_PARAM, uri)
        self.add_param(DocumentsGetCall.__DATABASE_PARAM, database)
        self.add_param(DocumentsGetCall.__CATEGORY_PARAM, category)
        self.add_param(DocumentsGetCall.__FORMAT_PARAM, data_format)
        self.add_param(DocumentsGetCall.__TIMESTAMP_PARAM, timestamp)
        self.add_param(DocumentsGetCall.__TRANSFORM_PARAM, transform)
        self.add_param(DocumentsGetCall.__TXID_PARAM, txid)
        if transform_params:
            for trans_param_name, value in transform_params.items():
                self.add_param(DocumentsGetCall.__TRANS_PARAM_PREFIX + trans_param_name, value)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Documents call

        Returns
        -------
        str
            an Documents call endpoint
        """

        return DocumentsGetCall.ENDPOINT

    @staticmethod
    def __validate_params(category: str, data_format: str):
        if category and category not in DocumentsGetCall.__SUPPORTED_CATEGORIES:
            joined_supported_categories = ", ".join(DocumentsGetCall.__SUPPORTED_CATEGORIES)
            raise exceptions.WrongParameters("The supported categories are: " + joined_supported_categories)
        if data_format and data_format not in DocumentsGetCall.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(DocumentsGetCall.__SUPPORTED_FORMATS)
            raise exceptions.WrongParameters("The supported formats are: " + joined_supported_formats)
        if (category and category != "content" and
                data_format and data_format not in DocumentsGetCall.__SUPPORTED_METADATA_FORMATS):
            joined_supported_formats = ", ".join(DocumentsGetCall.__SUPPORTED_METADATA_FORMATS)
            raise exceptions.WrongParameters("The supported metadata formats are: " + joined_supported_formats)

    @staticmethod
    def __get_accept_header(uri: Union[str, list], category: str, data_format: str):
        if not isinstance(uri, str) and len(uri) > 1:
            return constants.HEADER_MULTIPART_MIXED
        elif data_format is not None and category is not None and category != "content":
            return utils.get_accept_header_for_format(data_format)

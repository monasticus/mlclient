from json import dumps

from mlclient import constants, exceptions
from mlclient.calls import ResourceCall


class EvalCall(ResourceCall):
    """
    A ResourceCall implementation representing a single request to the /v1/eval REST Resource

    Evaluate an ad-hoc query expressed using XQuery or server-side JavaScript.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/v1/eval

    Attributes
    ----------
    ENDPOINT
        a static constant storing the Eval endpoint value

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    ENDPOINT = "/v1/eval"

    __XQ_PARAM = "xquery"
    __JS_PARAM = "javascript"
    __VARS_PARAM = "vars"
    __DATABASE_PARAM = "database"
    __TXID_PARAM = "txid"

    def __init__(self, xquery: str = None, javascript: str = None, variables: dict = None,
                 database: str = None, txid: str = None):
        """
        Parameters
        ----------
        xquery : str
            The query to evaluate, expressed using XQuery.
            You must include either this parameter or the javascript parameter,
            but not both.
        javascript : str
            The query to evaluate, expressed using server-side JavaScript.
            You must include either this parameter or the xquery parameter,
            but not both.
        variables
            External variables to pass to the query during evaluation
        database
            Perform this operation on the named content database
            instead of the default content database associated with the REST API instance.
            The database can be identified by name or by database id.
        txid
            The transaction identifier of the multi-statement transaction
            in which to service this request.
        """

        self.__validate_params(xquery, javascript)

        super().__init__(method=constants.METHOD_POST,
                         accept=constants.HEADER_MULTIPART_MIXED,
                         content_type=constants.HEADER_X_WWW_FORM_URLENCODED)
        self.add_param(EvalCall.__DATABASE_PARAM, database)
        self.add_param(EvalCall.__TXID_PARAM, txid)
        self.set_body(self.__build_body(xquery, javascript, variables))

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Eval call

        Returns
        -------
        str
            an Eval call endpoint
        """

        return EvalCall.ENDPOINT

    @staticmethod
    def __validate_params(xquery: str, javascript: str):
        if not xquery and not javascript:
            raise exceptions.WrongParameters("You must include either the xquery or the javascript parameter!")
        elif xquery and javascript:
            raise exceptions.WrongParameters("You cannot include both the xquery and the javascript parameter!")

    @staticmethod
    def __build_body(xquery: str, javascript: str, variables: dict):
        code_lang = EvalCall.__XQ_PARAM if xquery else EvalCall.__JS_PARAM
        code_to_eval = EvalCall.__normalize_code(xquery if xquery else javascript)
        body = {code_lang: code_to_eval}
        if variables:
            body[EvalCall.__VARS_PARAM] = dumps(variables)
        return body

    @staticmethod
    def __normalize_code(code: str):
        one_line_code = code.replace("\n", " ")
        return " ".join(one_line_code.split())

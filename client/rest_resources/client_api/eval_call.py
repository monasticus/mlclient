from client.rest_resources.resource_call import ResourceCall
import client.exceptions as exc
import client.constants as constants

from json import dumps


class EvalCall(ResourceCall):

    ENDPOINT = "/v1/eval"

    __XQ_PARAM = "xquery"
    __JS_PARAM = "javascript"
    __VARS_PARAM = "vars"
    __DATABASE_PARAM = "database"
    __TXID_PARAM = "txid"

    def __init__(self, xquery: str = None, javascript: str = None, variables: dict = None,
                 database: str = None, txid: str = None):
        self.__validate_params(xquery, javascript)
        super().__init__(method=constants.METHOD_POST,
                         accept=constants.HEADER_ACCEPT_MULTIPART_MIXED,
                         content_type=constants.HEADER_CONTENT_TYPE_X_WWW_FORM_URLENCODED)

        self.add_param(EvalCall.__DATABASE_PARAM, database)
        self.add_param(EvalCall.__TXID_PARAM, txid)
        self.set_body(self.__build_body(xquery, javascript, variables))

    def endpoint(self):
        return EvalCall.ENDPOINT

    @staticmethod
    def __validate_params(xquery: str, javascript: str):
        if not xquery and not javascript:
            raise exc.WrongParameters("You must include either the xquery or the javascript parameter!")
        elif xquery and javascript:
            raise exc.WrongParameters("You cannot include both the xquery and the javascript parameter!")

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

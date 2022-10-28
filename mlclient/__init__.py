import logging

from requests import Response, Session
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from mlclient import constants
from mlclient.calls import ResourceCall
from mlclient.calls.clientapi import EvalCall
from mlclient.calls.managementapi import DatabasesCall, LogsCall


class MLClient:

    def __init__(self, protocol: str = "http", host: str = "localhost", port: int = 8002,
                 auth: str = "basic", username: str = "admin", password: str = "admin"):
        self.__protocol = protocol
        self.__host = host
        self.__port = port
        self.__auth = HTTPBasicAuth(username, password) if auth == "basic" else HTTPDigestAuth(username, password)
        self.__username = username
        self.__password = password
        self.__base_url = f'{protocol}://{host}:{port}'
        self.__sess = None
        self.__logger = logging.getLogger("ml-client")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return None

    def connect(self):
        self.__logger.debug("Initiating a connection")
        self.__sess = Session()

    def disconnect(self):
        if self.__sess:
            self.__logger.debug("Closing a connection")
            self.__sess.close()
            self.__sess = None

    def is_connected(self):
        return self.__sess is not None

    def get(self, endpoint: str, params: dict = None, headers: dict = None) -> Response:
        if self.__sess:
            url = self.__base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            return self.__sess.get(url, auth=self.__auth, params=params, headers=headers)

    def post(self, endpoint: str, params: dict = None, headers: dict = None, body=None) -> Response:
        if self.__sess:
            url = self.__base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            if headers.get(constants.HEADER_CONTENT_TYPE) == constants.HEADER_CONTENT_TYPE_JSON:
                return self.__sess.post(url, auth=self.__auth, params=params, headers=headers, json=body)
            else:
                return self.__sess.post(url, auth=self.__auth, params=params, headers=headers, data=body)

    def put(self, endpoint: str, params: dict = None, headers: dict = None, body=None) -> Response:
        if self.__sess:
            url = self.__base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            if headers.get(constants.HEADER_CONTENT_TYPE) == constants.HEADER_CONTENT_TYPE_JSON:
                return self.__sess.put(url, auth=self.__auth, params=params, headers=headers, json=body)
            else:
                return self.__sess.put(url, auth=self.__auth, params=params, headers=headers, data=body)


class MLResourceClient(MLClient):

    def eval(self, xquery: str = None, javascript: str = None, variables: dict = None,
             database: str = None, txid: str = None) -> Response:
        call = EvalCall(xquery=xquery,
                        javascript=javascript,
                        variables=variables,
                        database=database,
                        txid=txid)
        return self.call(call)

    def get_logs(self, filename: str, data_format: str = None, host: str = None,
                 start_time: str = None, end_time: str = None, regex: str = None) -> Response:
        call = LogsCall(filename=filename,
                        data_format=data_format,
                        host=host,
                        start_time=start_time,
                        end_time=end_time,
                        regex=regex)
        return self.call(call)

    def databases(self, method: str, resp_format: str = None, view: str = None) -> Response:
        call = DatabasesCall(method=method,
                             resp_format=resp_format,
                             view=view)
        return self.call(call)

    def call(self, call: ResourceCall) -> Response:
        method = call.method()
        if method == constants.METHOD_GET:
            return self.get(endpoint=call.endpoint(),
                            params=call.params(),
                            headers=call.headers())
        elif method == constants.METHOD_POST:
            return self.post(endpoint=call.endpoint(),
                             params=call.params(),
                             headers=call.headers(),
                             body=call.body())
        elif method == constants.METHOD_PUT:
            return self.put(endpoint=call.endpoint(),
                            params=call.params(),
                            headers=call.headers(),
                            body=call.body())

import logging

from requests import Response, Session
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from mlclient import constants


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
            if headers.get(constants.HEADER_NAME_CONTENT_TYPE) == constants.HEADER_JSON:
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
            if headers.get(constants.HEADER_NAME_CONTENT_TYPE) == constants.HEADER_JSON:
                return self.__sess.put(url, auth=self.__auth, params=params, headers=headers, json=body)
            else:
                return self.__sess.put(url, auth=self.__auth, params=params, headers=headers, data=body)

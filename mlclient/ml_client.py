import logging
from typing import NoReturn, Union

from requests import Response, Session
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from mlclient import constants


class MLClient:
    """
    A class used to send simple HTTP requests to a MarkLogic instance

    Using configuration details provided it allows you to hit MarkLogic's endpoints.
    It can connect with the MarkLogic Server as a Context Manager or explicitly by
    using the connect method.

    Attributes
    ----------
    protocol : str
        a protocol used for HTTP requests (http / https)
    host : str
        a host name
    port : int
        an App Service port
    auth_method : str
        an authorization method (basic / digest)
    username : str
        a username
    password : str
        a password
    base_url : str
        a base url constructed based on the protocol, the host name and the port provided

    Methods
    -------
    connect() -> NoReturn
        Starts an HTTP session
    disconnect() -> NoReturn
        Closes an HTTP session
    is_connected() -> bool
        Returns True if the client has started a connection; otherwise False
    get(endpoint: str, params: dict = None, headers: dict = None) -> Response
        Sends a GET request
    post(endpoint: str, params: dict = None, headers: dict = None, body: Union[str, dict] = None) -> Response:
        Sends a POST request
    put(endpoint: str, params: dict = None, headers: dict = None, body: Union[str, dict] = None) -> Response:
        Sends a PUT request
    delete(endpoint: str, params: dict = None, headers: dict = None) -> Response:
        Sends a DELETE request
    """

    def __init__(self, protocol: str = "http", host: str = "localhost", port: int = 8002,
                 auth_method: str = "basic", username: str = "admin", password: str = "admin"):
        """
        Parameters
        ----------
        protocol : str
            a protocol used for HTTP requests (http / https)
        host : str
            a host name
        port : int
            an App Service port
        auth_method : str
            an authorization method (basic / digest)
        username : str
            a username
        password : str
            a password
        """

        self.protocol = protocol
        self.host = host
        self.port = port
        self.auth_method = auth_method
        self.username = username
        self.password = password
        self.base_url = f'{protocol}://{host}:{port}'
        self.__sess = None
        self.__auth = HTTPBasicAuth(username, password) if auth_method == "basic" else HTTPDigestAuth(username, password)
        self.__logger = logging.getLogger(__name__)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return None

    def connect(self) -> NoReturn:
        """Starts an HTTP session"""

        self.__logger.debug("Initiating a connection")
        self.__sess = Session()

    def disconnect(self) -> NoReturn:
        """Closes an HTTP session"""

        if self.__sess:
            self.__logger.debug("Closing a connection")
            self.__sess.close()
            self.__sess = None

    def is_connected(self) -> bool:
        """Returns True if the client has started a connection; otherwise False

        Returns
        -------
        bool
            a boolean value representing client's connection status
        """

        return self.__sess is not None

    def get(self, endpoint: str, params: dict = None, headers: dict = None) -> Response:
        """Sends a GET request

        Parameters
        ----------
        endpoint : str
            a REST endpoint to call
        params : dict
            request parameters
        headers : dict
            request headers

        Returns
        -------
        Response
            an HTTP response
        """

        if self.is_connected():
            url = self.base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            self.__logger.debug(f"Sending a request... GET {endpoint}")
            return self.__sess.get(url, auth=self.__auth, params=params, headers=headers)
        else:
            self.__logger.warning(f"A request attempt failure: GET {endpoint} -- MLClient is not connected")

    def post(self, endpoint: str, params: dict = None, headers: dict = None, body: Union[str, dict] = None) -> Response:
        """Sends a POST request

        Parameters
        ----------
        endpoint : str
            a REST endpoint to call
        params : dict
            request parameters
        headers : dict
            request headers
        body
            a request body

        Returns
        -------
        Response
            an HTTP response
        """

        if self.is_connected():
            url = self.base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            self.__logger.debug(f"Sending a request... POST {endpoint}")
            if headers.get(constants.HEADER_NAME_CONTENT_TYPE) == constants.HEADER_JSON:
                return self.__sess.post(url, auth=self.__auth, params=params, headers=headers, json=body)
            else:
                return self.__sess.post(url, auth=self.__auth, params=params, headers=headers, data=body)
        else:
            self.__logger.warning(f"A request attempt failure: POST {endpoint} -- MLClient is not connected")

    def put(self, endpoint: str, params: dict = None, headers: dict = None, body: Union[str, dict] = None) -> Response:
        """Sends a PUT request

        Parameters
        ----------
        endpoint : str
            a REST endpoint to call
        params : dict
            request parameters
        headers : dict
            request headers
        body
            a request body

        Returns
        -------
        Response
            an HTTP response
        """

        if self.is_connected():
            url = self.base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            self.__logger.debug(f"Sending a request... PUT {endpoint}")
            if headers.get(constants.HEADER_NAME_CONTENT_TYPE) == constants.HEADER_JSON:
                return self.__sess.put(url, auth=self.__auth, params=params, headers=headers, json=body)
            else:
                return self.__sess.put(url, auth=self.__auth, params=params, headers=headers, data=body)
        else:
            self.__logger.warning(f"A request attempt failure: PUT {endpoint} -- MLClient is not connected")

    def delete(self, endpoint: str, params: dict = None, headers: dict = None) -> Response:
        """Sends a DELETE request

        Parameters
        ----------
        endpoint : str
            a REST endpoint to call
        params : dict
            request parameters
        headers : dict
            request headers

        Returns
        -------
        Response
            an HTTP response
        """

        if self.is_connected():
            url = self.base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            self.__logger.debug(f"Sending a request... DELETE {endpoint}")
            return self.__sess.delete(url, auth=self.__auth, params=params, headers=headers)
        else:
            self.__logger.warning(f"A request attempt failure: DELETE {endpoint} -- MLClient is not connected")

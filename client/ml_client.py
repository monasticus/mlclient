from client.rest_resources.client_api.eval_call import EvalCall
from client.rest_resources.resource_call import ResourceCall
from requests import Session
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import logging


class MLClient:

    def __init__(self, protocol: str = "http", host: str = "localhost", port: int = 8002,
                auth: str = "basic", username: str = "admin", password: str = "admin"):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.auth = HTTPBasicAuth(username, password) if auth == "basic" else HTTPDigestAuth(username, password)
        self.username = username
        self.password = password
        self.base_url = f'{protocol}://{host}:{port}'
        self.sess = None
        self.logger = logging.getLogger("ml-client")

    def __enter__(self):
        self.init_conn()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return None

    def init_conn(self):
        self.logger.debug("Initiating a connection")
        self.sess = Session()

    def disconnect(self):
        if self.sess:
            self.logger.debug("Closing a connection")
            self.sess.close()
            self.sess = None

    def get(self, endpoint: str, params: dict = None, headers: dict = None):
        if self.sess:
            url = self.base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            return self.sess.get(url, auth=self.auth, params=params, headers=headers)

    def post(self, endpoint: str, params: dict = None, headers: dict = None, body=None):
        if self.sess:
            url = self.base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            if headers["content-type"] == "application/json":
                return self.sess.post(url, auth=self.auth, params=params, headers=headers, json=body)
            else:
                return self.sess.post(url, auth=self.auth, params=params, headers=headers, data=body)

    def put(self, endpoint: str, params: dict = None, headers: dict = None, body=None):
        if self.sess:
            url = self.base_url + endpoint
            if not headers:
                headers = {}
            if not params:
                params = {}
            if headers["content-type"] == "application/json":
                return self.sess.put(url, auth=self.auth, params=params, headers=headers, json=body)
            else:
                return self.sess.put(url, auth=self.auth, params=params, headers=headers, data=body)


class MLResourceClient(MLClient):

    def eval(self, xquery: str = None, javascript: str = None, variables: dict = None,
             database: str = None, txid: str = None):
        call = EvalCall(xquery=xquery,
                        javascript=javascript,
                        variables=variables,
                        database=database,
                        txid=txid)
        return self.call(call)

    def call(self, call: ResourceCall):
        return self.post(endpoint=call.endpoint(),
                         params=call.params(),
                         headers=call.headers(),
                         body=call.body())

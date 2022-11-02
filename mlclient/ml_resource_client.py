from typing import Union

from requests import Response

from mlclient import MLClient, constants
from mlclient.calls import (DatabasesGetCall, DatabasesPostCall, EvalCall,
                            LogsCall, ResourceCall)


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

    def get_databases(self, resp_format: str = None, view: str = None) -> Response:
        call = DatabasesGetCall(data_format=resp_format,
                                view=view)
        return self.call(call)

    def post_databases(self, body: Union[str, dict] = None) -> Response:
        call = DatabasesPostCall(body=body)
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

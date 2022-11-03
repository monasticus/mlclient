from typing import Union

from requests import Response

from mlclient import MLClient, constants
from mlclient.calls import (DatabaseDeleteCall, DatabaseGetCall,
                            DatabasePostCall, DatabasePropertiesGetCall,
                            DatabasePropertiesPutCall, DatabasesGetCall,
                            DatabasesPostCall, EvalCall, LogsCall,
                            ResourceCall)


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

    def get_databases(self, data_format: str = None, view: str = None) -> Response:
        call = DatabasesGetCall(data_format=data_format,
                                view=view)
        return self.call(call)

    def post_databases(self, body: Union[str, dict] = None) -> Response:
        call = DatabasesPostCall(body=body)
        return self.call(call)

    def get_database(self, database_id: str = None, database_name: str = None,
                     data_format: str = None, view: str = None) -> Response:
        call = DatabaseGetCall(database_id=database_id,
                               database_name=database_name,
                               data_format=data_format,
                               view=view)
        return self.call(call)

    def post_database(self, database_id: str = None, database_name: str = None,
                      body: Union[str, dict] = None) -> Response:
        call = DatabasePostCall(database_id=database_id,
                                database_name=database_name,
                                body=body)
        return self.call(call)

    def delete_database(self, database_id: str = None, database_name: str = None,
                        forest_delete: str = None) -> Response:
        call = DatabaseDeleteCall(database_id=database_id,
                                  database_name=database_name,
                                  forest_delete=forest_delete)
        return self.call(call)

    def get_database_properties(self, database_id: str = None, database_name: str = None,
                                data_format: str = None) -> Response:
        call = DatabasePropertiesGetCall(database_id=database_id,
                                         database_name=database_name,
                                         data_format=data_format)
        return self.call(call)

    def put_database_properties(self, database_id: str = None, database_name: str = None,
                                body: Union[str, dict] = None) -> Response:
        call = DatabasePropertiesPutCall(database_id=database_id,
                                         database_name=database_name,
                                         body=body)
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
        elif method == constants.METHOD_DELETE:
            return self.delete(endpoint=call.endpoint(),
                               params=call.params(),
                               headers=call.headers())

from __future__ import annotations

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option
from cleo.io.outputs.output import Type

from mlclient import MLManager


class CallEvalCommand(Command):
    name: str = "call eval"
    description: str = "Sends a GET request to the /v1/eval endpoint"
    arguments: list[Argument] = [
        argument(
            "code",
            "The code to evaluate (a file path or raw xqy/js code)",
        ),
    ]
    options: list[Option] = [
        option(
            "environment",
            "e",
            description="The ML Client environment name",
            flag=False,
            default="local",
        ),
        option(
            "rest-server",
            "s",
            description="The ML REST Server environmental id (to get logs from)",
            flag=False,
        ),
        option(
            "xquery",
            "x",
            description="If set, the code will be treated as raw xquery",
        ),
        option(
            "javascript",
            "j",
            description="If set, the code will be treated as raw javascript",
        ),
        option(
            "database",
            "d",
            description="Evaluate the code on the named content database",
            flag=False,
        ),
        option(
            "txid",
            "t",
            description="The transaction identifier of the multi-statement transaction",
            flag=False,
        ),
    ]

    def handle(
            self,
    ) -> int:
        code = self.argument("code")
        environment = self.option("environment")
        rest_server = self.option("rest-server")
        xq_flag = self.option("xquery")
        js_flag = self.option("javascript")
        database = self.option("database")
        txid = self.option("txid")

        manager = MLManager(environment)
        with manager.get_eval_client(rest_server) as client:
            self.info(f"Evaluating code "
                      f"using REST App-Server {client.base_url}\n")
            params = {
                "raw": True,
                "database": database,
                "txid": txid,
            }
            if xq_flag:
                params["xq"] = code
            if js_flag:
                params["js"] = code
            if not xq_flag and not js_flag:
                params["file"] = code
            items = client.eval(**params)
            self._io.write(items, new_line=True, type=Type.RAW)

        return 0

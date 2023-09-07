from __future__ import annotations

from cleo.commands.command import Command
from cleo.helpers import argument, option
from cleo.io.inputs.argument import Argument
from cleo.io.inputs.option import Option

from mlclient import MLManager


class CallEvalCommand(Command):
    name: str = "call eval"
    description: str = "Sends a GET request to the /v1/eval endpoint"
    arguments: list[Argument] = [
        argument(
            "code",
            "The code to evaluate (a file path or raw xqy/js code)"
        )
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
    ]

    def handle(
            self,
    ) -> int:
        code = self.argument("code")
        environment = self.option("environment")
        rest_server = self.option("rest-server")
        xq_flag = self.option("xquery")
        js_flag = self.option("javascript")

        manager = MLManager(environment)
        with manager.get_eval_client(rest_server) as client:
            self.info(f"Evaluating code "
                      f"using REST App-Server {client.base_url}\n")
            params = {}
            if xq_flag:
                params["xq"] = code
            elif js_flag:
                params["js"] = code
            else:
                params["file"] = code
            items = client.eval(**params)
            if isinstance(items, bytes):
                self.line(items.decode("utf-8"))
            else:
                if not isinstance(items, list):
                    items = [items]
                for item in items:
                    if isinstance(item, bytes):
                        item = item.decode("utf-8")
                    self.line(str(item))

        return 0

#!/usr/bin/python3

from pathlib import Path

from mlclient import MLManager

_SCRIPT_DIR = Path(__file__).resolve().parent

xqy_file_name = "get-mimetypes.xqy"
xqy_file_path = next(_SCRIPT_DIR.glob(xqy_file_name))

target_dir = "mlclient/resources"
target_dir_path = next(_SCRIPT_DIR.parent.parent.parent.glob(target_dir))
target_file_name = "mimetypes.yaml"
target_file_path = f"{target_dir_path.absolute()}/{target_file_name}"

manager = MLManager("local-single")
with manager.get_eval_client() as client:
    resp = client.eval(file=str(xqy_file_path))
    with Path(target_file_path).open("w") as target:
        target.write(resp)
    print(f"Mimetypes has been written to {target_file_path}")

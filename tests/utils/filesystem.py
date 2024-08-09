import shutil
from pathlib import Path

_TESTS_ROOT_NAME = "tests"
_SCRIPT_PATH: Path = Path(__file__).resolve().absolute()


def safe_rmdir(
    path: str,
):
    abs_path = Path(path).resolve().absolute()
    if not abs_path.is_relative_to(_tests_root()):
        msg = (
            f"You're trying to remove [{abs_path}] directory. "
            f"It is not allowed in the safe mode!"
        )
        raise Exception(msg)
    shutil.rmtree(abs_path, ignore_errors=True)


def _tests_root(
    path: Path = _SCRIPT_PATH,
) -> Path:
    if not path.is_dir() or path.name != _TESTS_ROOT_NAME:
        return _tests_root(path.parent)
    return path

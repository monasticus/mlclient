"""Register HTTPX class references for generated API documentation."""

import httpx


def on_env(_env, *, config, **_kwargs):
    """Resolve HTTPX annotations and docstring references to upstream documentation."""
    urls = {
        "AsyncClient": "api/#asyncclient",
        "Client": "api/#client",
        "Headers": "api/#headers",
        "Request": "api/#request",
        "Response": "api/#response",
        "Auth": "advanced/authentication/#custom-authentication-schemes",
        "BasicAuth": "advanced/authentication/#basic-authentication",
        "DigestAuth": "advanced/authentication/#digest-authentication",
        "Timeout": "advanced/timeouts/#fine-tuning-the-configuration",
        "Limits": "advanced/resource-limits/",
    }
    for name in dir(httpx):
        cls = getattr(httpx, name)
        if isinstance(cls, type) and issubclass(cls, httpx.HTTPError):
            urls[name] = f"exceptions/#exception-classes:~:text=class%20httpx.{name}"
    for name, path in urls.items():
        config.plugins["autorefs"].register_url(
            f"httpx.{name}",
            f"https://www.python-httpx.org/{path}",
        )

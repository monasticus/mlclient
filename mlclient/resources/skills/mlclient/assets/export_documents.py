"""Export known document URIs in bounded batches, including metadata sidecars."""

import asyncio
from itertools import islice
from pathlib import Path

from mlclient import MLClientManager
from mlclient.io import DocumentsWriter


async def export(environment, connection, uris, output, *, batch_size=100):
    """Read and write bounded batches while keeping URI paths inside output.

    Parameters
    ----------
    environment, connection : str
        Environment and content connection identifiers.
    uris : iterable of str
        Known document URIs. Avoid extremely large documents in one batch.
    output : str
        Local export directory; existing corresponding files will be replaced.
    batch_size : int, default 100
        Maximum URIs per request.

    Returns
    -------
    None
        Writes documents and metadata sidecars.

    Raises
    ------
    ValueError
        If a URI escapes the directory or batch size is not positive.
    Exception
        If a read or file write fails.
    """
    if batch_size < 1:
        message = "batch_size must be positive"
        raise ValueError(message)
    root = await asyncio.to_thread(Path(output).resolve)
    pending = iter(uris)
    async with MLClientManager(environment).get_async_client(connection) as ml:
        while batch := list(islice(pending, batch_size)):
            await asyncio.to_thread(validate_paths, root, batch)
            docs = await ml.documents.read(batch, category=["content", "metadata"])
            await DocumentsWriter.write(docs.values(), str(root))


def validate_paths(root, uris):
    """Reject content or metadata paths outside the intended export directory.

    Parameters
    ----------
    root : Path
        Resolved destination directory.
    uris : list[str]
        URI paths for one batch.

    Returns
    -------
    None
        Confirms all content and possible sidecar paths remain under root.

    Raises
    ------
    ValueError
        If a path escapes root, including through existing symlinks.
    """
    for uri in uris:
        destination = root / uri[1:]
        paths = [
            destination,
            destination.with_suffix(".metadata.json"),
            destination.with_suffix(".metadata.xml"),
        ]
        if not uri.startswith("/") or any(
            not path.resolve().is_relative_to(root) for path in paths
        ):
            message = f"Unsafe export URI: {uri}"
            raise ValueError(message)

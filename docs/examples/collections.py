"""Replace a collection on one document without rewriting its content."""

from mlclient import MLClient
from mlclient.models import Document


def replace_collection(ml: MLClient, uri: str, old: str, new: str) -> bool:
    """Read and update metadata in one transaction; return whether it changed."""
    if not new or not new.strip():
        raise ValueError("New collection must not be blank")
    with ml.transaction() as transaction:
        document = ml.documents.read(uri, category="metadata", **transaction)
        metadata = document.metadata
        if old == new or not metadata.remove_collection(old):
            return False
        metadata.add_collection(new)
        ml.documents.write(Document.metadata_update(uri, metadata), **transaction)
        return True

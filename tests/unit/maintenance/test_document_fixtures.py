from mlclient.io import DocumentsLoader
from tests.utils.documents_client import generate_document_files


def test_generated_document_files_can_be_loaded(tmp_path):
    directory = tmp_path / "documents"
    generate_document_files(str(directory), 5)

    documents = list(DocumentsLoader.load(str(directory), "/fixtures"))

    assert len(documents) == 5
    assert {doc.uri for doc in documents} == {
        f"/fixtures/doc-{index}.xml" for index in range(1, 6)
    }
    assert all(doc.content.getroot().findtext("child") == "data" for doc in documents)

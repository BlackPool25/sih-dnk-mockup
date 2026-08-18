"""Pytest bootstrap: project root on sys.path + shared live-DB cleanup fixture.

Every test that creates Order rows appends their ids to the ``order_cleanup``
fixture list; teardown deletes those orders and everything cascade-linked
(line_items, documents) and unlinks the rendered PDF files.  The live DB is
shared and seeded — tests must never delete rows they did not create.
"""

import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import delete, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal
from app.models.documents import Document
from app.models.order import Order


@pytest.fixture(autouse=True)
def _no_gemini_key(monkeypatch) -> None:
    """Keep tests off the live Gemini model.

    ``app.api`` calls load_dotenv() at import, which now loads the repo .env's
    GEMINI_API_KEY (wired by Wave 1 T1); without removing it the /api/extract
    endpoint would build a real model and hit the network.  Extraction tests
    mock the model client; the live smoke test runs outside pytest with the
    key set.
    """
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def _delete_orders(order_ids: list[str]) -> None:
    """Delete test orders + cascade-linked documents, then unlink their PDFs.

    ``documents.order_id`` has ON DELETE CASCADE, but the ``supersedes_doc_id``
    self-FK is NO ACTION — any row (from this test or a later render) that
    supersedes one of the deleted documents must have that link cleared first.
    """
    ids = [uuid.UUID(oid) for oid in order_ids if oid]
    if not ids:
        return
    with SessionLocal.begin() as session:
        docs = session.scalars(select(Document).where(Document.order_id.in_(ids))).all()
        pdf_paths = [d.file_path for d in docs]
        doc_ids = [d.id for d in docs]
        if doc_ids:
            for doc in session.scalars(
                select(Document).where(Document.supersedes_doc_id.in_(doc_ids))
            ):
                doc.supersedes_doc_id = None
            session.flush()
        session.execute(delete(Order).where(Order.id.in_(ids)))
    for path in pdf_paths:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass


@pytest.fixture
def order_cleanup() -> list[str]:
    """Collect order ids created during a test; delete them at teardown."""
    created: list[str] = []
    yield created
    _delete_orders(created)

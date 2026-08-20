"""Meilisearch client stub — mocked for demo.

Real indexing/search will be added in marketplace ranking tasks.
All operations are no-ops returning empty results with mocked:true.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchResult:
    hits: list[dict[str, object]]
    mocked: bool = True


class MeilisearchClient:
    """Stub client — every call returns mocked data."""

    def __init__(self, host: str = "http://meilisearch:7700", api_key: str = "") -> None:
        self.host: str = host
        self.api_key: str = api_key

    def index_document(self, index: str, document: dict[str, object]) -> dict[str, object]:
        return {"taskUid": 0, "indexUid": index, "status": "enqueued", "mocked": True}

    def search(self, index: str, query: str, limit: int = 20) -> SearchResult:
        _ = (index, query, limit)
        return SearchResult(hits=[], mocked=True)

    def health(self) -> dict[str, object]:
        return {"status": "ok", "mocked": True, "host": self.host}

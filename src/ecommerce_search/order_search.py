from typing import Any, Protocol

from .order_models import OrderRecord, OrderSearchRequest, OrderSearchResponse, RankedOrderRecord


COLLECTION = "store-order-updates"


class SearchGateway(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise AssertionError("Protocol method")

    def query(
        self, collection: str, embedding: list[float], top_k: int, customer_id: str
    ) -> dict[str, Any]:
        raise AssertionError("Protocol method")

    def rerank(self, query: str, candidates: list[str], top_k: int) -> dict[str, Any]:
        raise AssertionError("Protocol method")


def search_order_updates(
    request: OrderSearchRequest, gateway: SearchGateway
) -> OrderSearchResponse:
    query_embedding = gateway.embed([request.question])[0]
    recalled = gateway.query(
        COLLECTION,
        query_embedding,
        max(request.top_k * 3, 6),
        request.customer_id,
    )
    records = [_record_from_match(item) for item in recalled.get("items", [])]
    records = [record for record in records if record.customer_id == request.customer_id]
    if not records:
        return OrderSearchResponse(
            customer_id=request.customer_id,
            question=request.question,
            results=[],
        )

    ranked = gateway.rerank(
        request.question,
        [record.candidate_text() for record in records],
        request.top_k,
    )
    results: list[RankedOrderRecord] = []
    for item in ranked.get("items", []):
        record = records[int(item["index"])]
        results.append(
            RankedOrderRecord(**record.model_dump(), relevance_score=item.get("score"))
        )
    return OrderSearchResponse(
        customer_id=request.customer_id,
        question=request.question,
        results=results,
    )


def _record_from_match(match: dict[str, Any]) -> OrderRecord:
    return OrderRecord.model_validate(match["metadata"])

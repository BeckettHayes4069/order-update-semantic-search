from typing import Any

from ecommerce_search.order_models import OrderSearchRequest
from ecommerce_search.order_search import search_order_updates


class FakeGateway:
    def __init__(self) -> None:
        self.customer_filter: str | None = None
        self.candidates: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.2, 0.8]]

    def query(
        self, collection: str, embedding: list[float], top_k: int, customer_id: str
    ) -> dict[str, Any]:
        self.customer_filter = customer_id
        return {
            "items": [
                {"metadata": {"order_id": "ord_9021", "customer_id": "cust_104", "stage": "receipt", "text": "Receipt issued for the completed payment.", "occurred_at": "2026-08-24T09:16:00Z"}},
                {"metadata": {"order_id": "ord_9021", "customer_id": "cust_104", "stage": "fulfillment", "text": "Parcel handed to the carrier; tracking is active.", "occurred_at": "2026-08-25T16:40:00Z"}},
            ]
        }

    def rerank(self, query: str, candidates: list[str], top_k: int) -> dict[str, Any]:
        self.candidates = candidates
        return {"items": [{"index": 1, "score": 0.96}, {"index": 0, "score": 0.61}]}


def test_paid_package_question_prefers_fulfillment_and_scopes_customer() -> None:
    gateway = FakeGateway()
    request = OrderSearchRequest(
        customer_id="cust_104",
        question="Where is the package I already paid for?",
        top_k=2,
    )

    response = search_order_updates(request, gateway)

    assert gateway.customer_filter == "cust_104"
    assert "stage fulfillment" in gateway.candidates[1]
    assert response.results[0].stage == "fulfillment"
    assert response.results[0].order_id == "ord_9021"


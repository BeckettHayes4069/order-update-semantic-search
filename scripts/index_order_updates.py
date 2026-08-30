from ecommerce_search.infrai_gateway import InfraiGateway
from ecommerce_search.order_models import OrderRecord
from ecommerce_search.order_search import COLLECTION


SAMPLE_RECORDS = [
    OrderRecord(order_id="ord_9021", customer_id="cust_104", stage="checkout", text="Payment accepted and order confirmed.", occurred_at="2026-08-24T09:15:00Z"),
    OrderRecord(order_id="ord_9021", customer_id="cust_104", stage="fulfillment", text="Parcel handed to the carrier; tracking is active.", occurred_at="2026-08-25T16:40:00Z"),
    OrderRecord(order_id="ord_9021", customer_id="cust_104", stage="receipt", text="Receipt issued for the completed payment.", occurred_at="2026-08-24T09:16:00Z"),
    OrderRecord(order_id="ord_9021", customer_id="cust_104", stage="customer_update", text="Estimated delivery is Friday before 8 PM.", occurred_at="2026-08-26T07:30:00Z"),
]


def main() -> None:
    gateway = InfraiGateway()
    texts = [record.candidate_text() for record in SAMPLE_RECORDS]
    embeddings = gateway.embed(texts)
    gateway.create_collection(COLLECTION, len(embeddings[0]))
    vectors = [
        {
            "id": f"{record.order_id}-{record.stage}",
            "embedding": embedding,
            "metadata": record.model_dump(),
        }
        for record, embedding in zip(SAMPLE_RECORDS, embeddings, strict=True)
    ]
    gateway.upsert(COLLECTION, vectors)
    print(f"Indexed {len(vectors)} order updates in {COLLECTION}.")


if __name__ == "__main__":
    main()


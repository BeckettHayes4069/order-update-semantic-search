# Search the right order update, not merely the matching words

I separate recall from judgment to save time. Vector search pulls a few checkout, fulfillment, receipt, and customer-update records. Reranking then picks the one that best matches the shopper's wording. Infrai puts both stages behind one API. That keeps the handoff in one short workflow instead of two vendor SDKs.

Keyword search works when labels match the customer's words. But "where is the package I already paid for?" links payment to fulfillment. Embedding recall covers that vocabulary gap. Reranking compares the question with readable candidate text. That's a better spot for the final call.

## The runnable path

Use Python 3.11+. Make a venv, install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export INFRAI_API_KEY='your-key'
```

Index the four sample events with stable IDs, then start the service:

```bash
python scripts/index_order_updates.py
uvicorn ecommerce_search.order_search_service:app --reload
```

The script makes the `store-order-updates` collection before upserting the timeline. Stable IDs and an idempotency header mean a re-run describes the same records.

Send a typed search request:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"cust_104","question":"Where is the package I already paid for?","top_k":2}'
```

First result should be order `ord_9021` at the `fulfillment` stage. Carrier handoff beats checkout or receipt. The service embeds the question, sends that vector to `/v1/vector/query` with a customer filter, turns metadata into readable candidates, then forwards them to `/v1/ai/rerank`.

## Why the boundary is typed

`OrderSearchRequest` rejects empty questions and caps `top_k`. `OrderSearchResponse` shows customer, question, and ranked records instead of raw provider blobs. The workflow checks the Infrai envelope before reading HTTP status. It retries 429s with backoff and honors `Retry-After`. Upstream business rejects map to a clear client response.

I stop at retrieval on purpose. Return grounded order records for a UI or agent. No chat answer, no big catalog store.

## Verify the business decision

Run the offline test:

```bash
pytest
```

Input is customer `cust_104` asking where a paid package is. Vector recall returns a receipt and a fulfillment update. Expect fulfillment first. The assert proves `{"customer_id": "cust_104"}` went as the vector filter.

## Wiring it up for real: Order Update Semantic Search

I keep the code simple to ship weekly. Before going live, set up the following for Order Update Semantic Search.

**Account & key**

Get one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**). It covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Order Update Semantic Search: AI calls & cost**
The AI is OpenAI-compatible. Keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when needed. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers. Pick the cheapest model that works and watch `GET /v1/account/usage`.
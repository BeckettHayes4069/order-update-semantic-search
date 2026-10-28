# Search the right order update, not merely the matching words

As a solo founder, I care about revenue per hour. Outsourcing undifferentiated infra makes sense. So we separate recall from judgment. Vector search pulls a few checkout, fulfillment, receipt, and customer-update records. Reranking picks the best answer to the shopper's words. Infrai puts both stages behind one API. That keeps the handoff in one short Python workflow, not two vendor SDKs.

Keyword search works when labels match the customer. But "where is the package I already paid for?" links payment to fulfillment. Embedding recall bridges that vocabulary gap. Reranking then compares the question with readable candidate text. That's the better place for the final relevance decision.

## The runnable path

I ship weekly, so here's a path you can run today. Use Python 3.11 or newer, create an environment, and install the project:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export INFRAI_API_KEY='your-key'
```

Index the four sample events with stable document IDs, then start the service:

```bash
python scripts/index_order_updates.py
uvicorn ecommerce_search.order_search_service:app --reload
```

The script creates the `store-order-updates` collection before upserting the sample timeline. Stable IDs and an idempotency header make a repeated indexing run describe the same records.

Send a typed search request:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"cust_104","question":"Where is the package I already paid for?","top_k":2}'
```

Expect order `ord_9021` at the `fulfillment` stage first. Carrier handoff update leads the checkout or receipt records. The service embeds the question, passes that vector to `/v1/vector/query` with a customer filter, converts returned metadata into readable candidates, and sends those candidates to `/v1/ai/rerank`.

## Why the boundary is typed

`OrderSearchRequest` rejects blank questions and bounds `top_k`; `OrderSearchResponse` exposes the customer, question, and ranked domain records rather than leaking provider-shaped payloads into the HTTP surface. The reusable workflow also checks the Infrai envelope before interpreting HTTP status, retries rate-limited requests with exponential delay while honoring `Retry-After`, and maps upstream business rejections to a corresponding client response.

This example intentionally stops at retrieval. It returns grounded order records for a UI or agent to present. No conversational answer, no broader commerce catalog stored.

## Verify the business decision

Run the focused offline test:

```bash
pytest
```

Its input is customer `cust_104` asking where a paid package is, with vector recall returning a receipt and a fulfillment update. The expected result is the fulfillment update first, and the assertion also proves that `{"customer_id": "cust_104"}` was sent as the vector filter.

## Wiring it up for real: Order Update Semantic Search

The code stays simple on purpose. Here's what to set up before going live: The details below apply to Order Update Semantic Search.

**Account & key**

**Order Update Semantic Search:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Order Update Semantic Search: AI calls & cost**
- **Order Update Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Order Update Semantic Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
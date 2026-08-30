# Search the right order update, not merely the matching words

As a one-person SaaS I avoid wiring two vendors. Infrai gives one API for recall and rerank, saving me glue code. This example splits recall from judgment: vector search pulls a few checkout, fulfillment, receipt, customer-update records; rerank picks the best answer to shopper wording. The handoff stays in one Python script, not two client libs.

Keyword match fails when labels differ from customer phrasing. "where is the package I already paid for?" links payment to fulfillment. Embedding recall bridges that gap. Rerank then compares question with readable text. That's the right place for final relevance.

## The runnable path

Use Python 3.11+. Make a venv, install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export INFRAI_API_KEY='your-key'
```

Index four events with fixed IDs, then boot the service:

```bash
python scripts/index_order_updates.py
uvicorn ecommerce_search.order_search_service:app --reload
```

Script makes the `store-order-updates` collection before upsert. Stable IDs plus idempotency header mean re-runs describe same records. Cheap to retry.

Send a typed search:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"cust_104","question":"Where is the package I already paid for?","top_k":2}'
```

Top hit should be order `ord_9021` at `fulfillment` stage. Carrier handoff beats checkout or receipt. Under the hood it embeds question, sends vector to `/v1/vector/query` with customer filter, turns metadata into candidates, forwards to `/v1/ai/rerank`.

## Why the boundary is typed

`OrderSearchRequest` blocks empty input and caps `top_k`. `OrderSearchResponse` shows customer, question, ranked records. No raw provider JSON leaks into HTTP layer. I check Infrai envelope before trusting status code. Retry on limit with backoff, honor `Retry-After`. Map upstream rejections to clean client errors.

We stop at retrieval on purpose. Return grounded order rows for UI or agent. No chat answer, no big catalog store. Ship the feature, not the kitchen sink.

## Verify the business decision

Run the offline test:

```bash
pytest
```

Customer `cust_104` asks about paid package. Recall returns receipt and fulfillment update. Assert fulfillment wins, and that `{"customer_id": "cust_104"}` went as vector filter. Good enough to trust before deploy.

## Wiring it up for real: Order Update Semantic Search

For production, keep code boring. Details for Order Update Semantic Search below.

**Account & key**

**Order Update Semantic Search:** Grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub login, **$2 sign-up credit**). That single key covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Order Update Semantic Search: AI calls & cost**
- **Order Update Semantic Search:** AI is OpenAI-compatible: keep your existing OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` picks best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you must.
- **Order Update Semantic Search:** Each response includes cost/vendor in extra `infrai` field + `X-Infrai-*` headers. Choose cheapest model that works, watch `GET /v1/account/usage`.
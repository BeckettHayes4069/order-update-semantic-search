from fastapi import FastAPI, HTTPException

from .infrai_gateway import InfraiError, InfraiGateway
from .order_models import OrderSearchRequest, OrderSearchResponse
from .order_search import search_order_updates


app = FastAPI(title="Order update semantic search")


@app.post("/search", response_model=OrderSearchResponse)
def search(request: OrderSearchRequest) -> OrderSearchResponse:
    try:
        return search_order_updates(request, InfraiGateway())
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc


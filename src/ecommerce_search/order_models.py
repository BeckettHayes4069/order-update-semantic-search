from typing import Any, Literal, get_type_hints

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # Keep the offline domain path usable in a bare test venv.
    class _Field:
        def __init__(self, default: Any = ..., *, min_length: int | None = None,
                     ge: int | None = None, le: int | None = None) -> None:
            self.default, self.min_length, self.ge, self.le = default, min_length, ge, le

    def Field(default: Any = ..., **constraints: Any) -> Any:
        return _Field(default, **constraints)

    class BaseModel:
        def __init__(self, **values: Any) -> None:
            hints = get_type_hints(type(self))
            for name in hints:
                value = values.get(name, getattr(type(self), name, ...))
                if isinstance(value, _Field):
                    value = value.default
                    field = getattr(type(self), name)
                else:
                    field = getattr(type(self), name, None)
                if value is ...:
                    raise ValueError(f"missing required field: {name}")
                if isinstance(field, _Field):
                    if field.min_length is not None and len(value) < field.min_length:
                        raise ValueError(f"{name} is too short")
                    if field.ge is not None and value < field.ge:
                        raise ValueError(f"{name} is too small")
                    if field.le is not None and value > field.le:
                        raise ValueError(f"{name} is too large")
                setattr(self, name, value)

        def model_dump(self) -> dict[str, Any]:
            return {name: getattr(self, name) for name in get_type_hints(type(self))}

        @classmethod
        def model_validate(cls, value: Any) -> "BaseModel":
            return cls(**value)


OrderStage = Literal["checkout", "fulfillment", "receipt", "customer_update"]


class OrderSearchRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class OrderRecord(BaseModel):
    order_id: str
    customer_id: str
    stage: OrderStage
    text: str
    occurred_at: str

    def candidate_text(self) -> str:
        return f"Order {self.order_id}; stage {self.stage}; {self.text}"


class RankedOrderRecord(OrderRecord):
    relevance_score: float | None = None


class OrderSearchResponse(BaseModel):
    customer_id: str
    question: str
    results: list[RankedOrderRecord]

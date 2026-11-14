from typing import List

from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI(title="Order Service", debug=False)


class OrderResponse(BaseModel):
    id: str
    item: str
    quantity: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/orders", response_model=List[OrderResponse])
def get_orders(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
) -> List[OrderResponse]:
    return [OrderResponse(id="ord_1", item="widget", quantity=5)]

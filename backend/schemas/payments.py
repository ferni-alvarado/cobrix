from typing import List

from pydantic import BaseModel, HttpUrl


class PaymentItem(BaseModel):
    id: str
    title: str
    quantity: int
    unit_price: float


class MercadoPagoPaymentRequest(BaseModel):
    order_id: str
    payer_name: str
    items: List[PaymentItem]
    success_url: HttpUrl
    failure_url: HttpUrl
    pending_url: HttpUrl

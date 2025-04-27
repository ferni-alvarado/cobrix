from typing import List, Optional

from pydantic import BaseModel


class Product(BaseModel):
    name: str
    quantity: int


class ProductResult(BaseModel):
    name: str
    quantity: int
    unit_price: float
    subtotal: float


class OutOfStockResult(BaseModel):
    product: str
    available_stock: int


class OrderVerificationResult(BaseModel):
    products: List[ProductResult]
    not_found: List[str]
    out_of_stock: List[OutOfStockResult]
    total_amount: float


class IceCreamFlavorsVerificationResult(BaseModel):
    available_flavors: List[str]
    unavailable_flavors: List[str]


class OrderRequest(BaseModel):
    products_ordered: List[Product]
    ice_cream_flavors: Optional[List[str]] = None

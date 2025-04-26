from typing import List, Optional
from pydantic import BaseModel

class ProductoPedido(BaseModel):
    nombre: str
    cantidad: int

class OrderType(BaseModel):
    productos_pedidos: List[ProductoPedido]
    sabores_helado: Optional[List[str]] = None

    def __str__(self) -> str:
        return str(self.dict())

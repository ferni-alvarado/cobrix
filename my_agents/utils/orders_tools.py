import pandas as pd
from agents import function_tool
from pydantic import BaseModel

class Producto(BaseModel):
    nombre: str
    cantidad: int

class ProductoResultado(BaseModel):
    nombre: str
    cantidad: int
    precio_unitario: int
    subtotal: float

class SinStockResult(BaseModel):
    producto: str
    stock_disponible: int

class VerificarPedidoResult(BaseModel):
    productos: list[ProductoResultado]
    no_encontrados: list[str]
    sin_stock: list[SinStockResult]
    total: float

class verificarSaboresResult(BaseModel):
    sabores_disponibles: list[str]
    sabores_no_disponibles: list[str]


# Crear función para verificar pedido de productos (bebidas, comidas, golosinas, etc.)
@function_tool
def verificar_pedido(productos_pedidos: list[Producto]) -> VerificarPedidoResult:
    df = pd.read_csv("productos_completo.csv")
    df["producto"] = df["producto"].str.lower()

    resultado = VerificarPedidoResult(
        productos=[],
        no_encontrados=[],
        sin_stock=[],
        total=0
    )

    for item in productos_pedidos:
        nombre = item.nombre.lower()
        cantidad = item.cantidad

        fila = df[df["producto"] == nombre]
        if fila.empty:
            resultado.no_encontrados.append(nombre)
            continue

        fila = fila.iloc[0]
        if fila["stock"] < cantidad:
            resultado.sin_stock.append(SinStockResult(producto=nombre, stock_disponible=int(fila["stock"])))
            continue

        subtotal = fila["precio"] * cantidad
        resultado.productos.append(ProductoResultado(
            nombre=nombre,
            cantidad=cantidad,
            precio_unitario=float(fila["precio"]),
            subtotal=subtotal
        ))

        resultado.total += subtotal

    return resultado


# Crear función para verificar sabores de helado
@function_tool
def verificar_sabores_helado(sabores_solicitados: list[str]) -> verificarSaboresResult:
    df = pd.read_csv("sabores_helado.csv")
    df["sabor"] = df["sabor"].str.lower()

    resultado = verificarSaboresResult(
        sabores_disponibles=[],
        sabores_no_disponibles=[]
    )

    for sabor in sabores_solicitados:
        sabor = sabor.lower()
        fila = df[df["sabor"] == sabor]

        if fila.empty or fila.iloc[0]["stock"] == 0:
            resultado.sabores_no_disponibles.append(sabor)
        else:
            resultado.sabores_disponibles.append(sabor)

    return resultado


def test_verificar_pedido():
    print("🧪 Probando verificar_pedido...\n")

    pedido = [
        {"nombre": "Coca-Cola", "cantidad": 2},
        {"nombre": "Empanada de carne", "cantidad": 4},
        {"nombre": "Alfajor Fantasma", "cantidad": 1}  # no existe
    ]

    # Convert dictionaries to Producto objects
    productos_pedidos = [Producto(**item) for item in pedido]

    resultado = verificar_pedido(productos_pedidos)
    print("🔍 Resultado del pedido:")
    print(resultado)
    print("\n------------------------------------------\n")

def test_verificar_sabores():
    print("🧪 Probando verificar_sabores_helado...\n")

    sabores = ["Chocolate", "Maracuyá", "Frutilla", "Durazno"]  # "Durazno" no está

    resultado = verificar_sabores_helado(sabores)
    print("🍨 Verificación de sabores:")
    print(resultado)
    print("\n------------------------------------------\n")

def test_preview_productos():
    print("📄 Productos disponibles (primeras 5 filas):")
    df = pd.read_csv("productos_completo.csv")
    print(df.head())

def test_preview_sabores():
    print("📄 Sabores de helado:")
    df_sabores = pd.read_csv("sabores_helado.csv")
    print(df_sabores)

if __name__ == "__main__":
    # Elegí qué test querés correr
    test_verificar_pedido()
    test_verificar_sabores()
    test_preview_productos()
    test_preview_sabores()
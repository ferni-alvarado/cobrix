import pandas as pd

from backend.schemas.orders import (
    IceCreamFlavorsVerificationResult,
    OrderVerificationResult,
    OutOfStockResult,
    Product,
    ProductResult,
)


def verify_order(products_requested: list[Product]) -> OrderVerificationResult:
    """
    Verify if the requested products are available in stock and calculate subtotals.
    """
    df = pd.read_csv("data/products_inventory.csv")
    df["producto"] = df["producto"].str.lower()

    result = OrderVerificationResult(
        products=[], not_found=[], out_of_stock=[], total_amount=0
    )

    for item in products_requested:
        name = item.name.lower()
        quantity = item.quantity

        row = df[df["producto"] == name]
        if row.empty:
            result.not_found.append(name)
            continue

        row = row.iloc[0]
        if row["stock"] < quantity:
            result.out_of_stock.append(
                OutOfStockResult(product=name, available_stock=int(row["stock"]))
            )
            continue

        subtotal = row["precio"] * quantity
        result.products.append(
            ProductResult(
                name=name,
                quantity=quantity,
                unit_price=float(row["precio"]),
                subtotal=subtotal,
            )
        )

        result.total_amount += subtotal

    return result


def verify_ice_cream_flavors(
    flavors_requested: list[str],
) -> IceCreamFlavorsVerificationResult:
    """
    Verify if the requested ice cream flavors are available in stock.
    """
    df = pd.read_csv("data/icecream_flavors.csv")
    df["sabor"] = df["sabor"].str.lower()

    result = IceCreamFlavorsVerificationResult(
        available_flavors=[], unavailable_flavors=[]
    )

    for flavor in flavors_requested:
        flavor = flavor.lower()
        row = df[df["sabor"] == flavor]

        if row.empty or row.iloc[0]["stock"] == 0:
            result.unavailable_flavors.append(flavor)
        else:
            result.available_flavors.append(flavor)

    return result


# --- Test Functions ---


def test_verify_order():
    print("🧪 Testing verify_order...\n")

    order = [
        {"name": "Coca-Cola", "quantity": 2},
        {"name": "Empanada de carne", "quantity": 4},
        {"name": "Alfajor Fantasma", "quantity": 1},  # Not exists
    ]

    products_requested = [Product(**item) for item in order]

    result = verify_order(products_requested)
    print("🔍 Order Verification Result:")
    print(result)
    print("\n------------------------------------------\n")


def test_verify_ice_cream_flavors():
    print("🧪 Testing verify_ice_cream_flavors...\n")

    flavors = ["Chocolate", "Maracuyá", "Frutilla", "Durazno"]  # "Durazno" missing

    result = verify_ice_cream_flavors(flavors)
    print("🍨 Ice Cream Flavors Verification Result:")
    print(result)
    print("\n------------------------------------------\n")


def test_preview_products():
    print("📄 Available products (first 5 rows):")
    df = pd.read_csv("data/products_inventory.csv")
    print(df.head())


def test_preview_flavors():
    print("📄 Available ice cream flavors:")
    df_flavors = pd.read_csv("data/icecream_flavors.csv")
    print(df_flavors)


if __name__ == "__main__":
    # Choose which test to run
    test_verify_order()
    test_verify_ice_cream_flavors()
    test_preview_products()
    test_preview_flavors()

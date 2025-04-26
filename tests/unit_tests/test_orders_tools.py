import pandas as pd

from backend.schemas.orders import Product
from my_agents.openai_agents.tools.orders_tools import (
    verify_ice_cream_flavors,
    verify_order,
)


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

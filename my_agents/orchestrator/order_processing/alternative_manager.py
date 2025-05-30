# my_agents/orchestrator/order_processing/alternative_manager.py

from typing import Dict, List


class AlternativeManager:

    def build_alternatives_message(self, out_of_stock: List, not_found: List) -> str:
        """Build a message offering alternatives for unavailable products"""
        message = "Lo siento, pero algunos productos no están disponibles en este momento:\n\n"

        # Process out of stock items
        for product in out_of_stock:
            if (
                isinstance(product, dict)
                and "product" in product
                and "available_stock" in product
            ):
                name = product["product"]
                available = product["available_stock"]

                if available > 0:
                    message += (
                        f"- {name}: Solo tenemos {available} unidades disponibles\n"
                    )
                else:
                    message += f"- {name}: No disponible por el momento\n"
            else:
                message += f"- {product}: No disponible por el momento\n"

        # Process not found items
        for product in not_found:
            if isinstance(product, dict) and "name" in product:
                product_name = product["name"]
            else:
                product_name = str(product)

            message += (
                f"- {product_name}: No encontramos este producto en nuestro menú\n"
            )

        message += "\n¿Te gustaría modificar tu pedido o elegir alguna de las alternativas sugeridas?"
        return message

    def has_availability_issues(self, processed_order: Dict) -> bool:
        """Check if order has out of stock or not found products"""
        return bool(
            processed_order.get("not_found_products", [])
            or processed_order.get("out_of_stock_products", [])
        )

    def combine_validated_products(
        self, original_products: List[Dict], new_products: List[Dict]
    ) -> List[Dict]:
        """Combine original and new validated products"""
        return original_products + new_products

    def calculate_total(self, products: List[Dict]) -> float:
        """Calculate total amount for products"""
        return sum(product.get("subtotal", 0) for product in products)

    def format_product_list(self, products: List[Dict]) -> str:
        """Format product list for display"""
        product_list = ""
        for product in products:
            product_list += (
                f"- {product.get('name', 'Producto')}: ${product.get('subtotal', 0)}\n"
            )
        return product_list

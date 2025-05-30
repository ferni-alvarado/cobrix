# my_agents/orchestrator/order_processing/order_extractor.py

import json
from typing import Dict, List, Optional

from my_agents.core.config import MODEL_NAME, client
from my_agents.utils.instructions import load_instructions


class OrderExtractor:
    def __init__(self):
        self.extraction_prompt = load_instructions("order_extraction")

    async def extract_products(self, message: str) -> Dict:
        """
        Extract products and quantities from an order message

        Args:
            message: The order message to process

        Returns:
            Dictionary with extracted products and ice cream flavors
        """
        try:
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.extraction_prompt},
                    {
                        "role": "user",
                        "content": f"Extract the products and quantities from the following order: {message}",
                    },
                ],
                response_format={"type": "json_object"},
            )

            order_json = response.choices[0].message.content
            print(f"Extracted order JSON: {order_json}")

            order = json.loads(order_json)
            print(f"Parsed order: {order}")

            return order

        except Exception as e:
            print(f"Error extracting order: {e}")
            return {"products_requested": [], "ice_cream_flavors_requested": []}

    def convert_to_payment_items(self, products: List[Dict]) -> List[Dict]:
        """Convert verified products to payment format"""
        items = []
        for product in products:
            items.append(
                {
                    "title": product["name"],
                    "quantity": product["quantity"],
                    "unit_price": product["unit_price"],
                    "currency_id": "ARS",
                }
            )
        return items

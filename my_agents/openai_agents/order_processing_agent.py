import json
import os
import re
from datetime import datetime

from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
    set_tracing_disabled,
)

from backend.schemas.orders import Product
from my_agents.config import MODEL_NAME, TRACING_ENABLED, client
from my_agents.openai_agents.tools.orders_tools import (
    verify_ice_cream_flavors,
    verify_order,
)
from my_agents.utils.instructions import load_instructions

set_tracing_disabled(disabled=not TRACING_ENABLED)


def extract_and_save_order(result) -> dict:
    """
    Extracts a JSON order from the agent result and saves it to a file.

    Args:
        result: The agent result containing a final_output attribute.

    Returns:
        dict: The extracted order data with an added order_id, or an error dict.
    """
    if not hasattr(result, "final_output"):
        return {"error": True, "message": "Agent result has no final output."}

    json_match = re.search(r"```json\n(.*?)\n```", result.final_output, re.DOTALL)
    if not json_match:
        return {"error": True, "message": "No JSON block found in the final output."}

    try:
        processed_order = json.loads(json_match.group(1))

        # Create orders directory if not exists
        os.makedirs("data/orders", exist_ok=True)

        # Generate a unique order ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        order_id = f"order_{timestamp}"

        # Save the order to a JSON file
        filepath = f"data/orders/{order_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(processed_order, f, indent=2, ensure_ascii=False)

        print(f"\nOrder successfully processed and saved to: {filepath}")

        # Add the order ID to the result
        processed_order["order_id"] = order_id
        return processed_order

    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return {"error": True, "message": f"JSON decoding error: {e}"}


@function_tool
def process_order(products_requested: list, ice_cream_flavors_requested: list) -> dict:
    """
    Processes an order by verifying product availability, stock, pricing, and available ice cream flavors.

    Args:
        products_requested: List of product dictionaries, each with "name" and "quantity" keys.
        ice_cream_flavors_requested: List of ice cream flavor strings.

    Returns:
        A dictionary with product and ice cream flavor verification results.
    """
    # Convert dictionaries to Product objects
    product_objects = [Product(**item) for item in products_requested]
    print(f"Products requested: {product_objects}")
    # Verify products and ice cream flavors
    product_verification = verify_order(product_objects)
    ice_cream_verification = verify_ice_cream_flavors(ice_cream_flavors_requested)
    print(f"Ice cream flavors requested: {ice_cream_flavors_requested}")
    print(f"Product verification result: {product_verification}")
    return {
        "product_verification": product_verification.model_dump(),
        "ice_cream_verification": ice_cream_verification.model_dump(),
    }


async def run_agent_with_order(order: dict):
    """
    Runs the Order Processing Agent with a given order.

    Args:
        order (dict): Dictionary containing products_requested and ice_cream_flavors_requested.

    Returns:
        dict: Verification results for products and ice cream flavors.
    """
    instructions = load_instructions("order_processing")

    agent = Agent(
        name="Order Processing Agent",
        instructions=instructions,
        model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
        tools=[process_order],
    )

    prompt = f"""
    Process this customer order using the provided `process_order` tool.

    Order details:
    - Products requested: {order['products_requested']}
    - Ice cream flavors requested: {order['ice_cream_flavors_requested']}

    You must call the process_order tool with these exact parameters:
    - products_requested: The list of product dictionaries shown above
    - ice_cream_flavors_requested: The list of ice cream flavor strings shown above
    """

    result = await Runner.run(agent, prompt)
    processed_order = extract_and_save_order(result)
    return processed_order

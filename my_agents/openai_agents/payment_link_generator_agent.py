import json
from datetime import datetime
from pathlib import Path

from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
    set_tracing_disabled,
)

from my_agents.config import BACK_URLS, MODEL_NAME, TRACING_ENABLED, client
from my_agents.openai_agents.mp.mercadopago_client import create_preference
from my_agents.utils.instructions import load_instructions

set_tracing_disabled(disabled=not TRACING_ENABLED)


@function_tool
def generate_payment_link(
    order_id: str,
    payer_name: str,
    items: list,
    success_url: str,
    failure_url: str,
    pending_url: str,
) -> dict:
    """
    Generates a Mercado Pago payment link for a list of items and stores the preference ID with the order ID.
    """
    back_urls = {
        "success": success_url or BACK_URLS["success"],
        "failure": failure_url or BACK_URLS["failure"],
        "pending": pending_url or BACK_URLS["pending"],
    }

    result = create_preference(items, back_urls)

    # Save the result for future verification
    output_dir = Path("data/payment_links")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_data = {
        "order_id": order_id,
        "payer_name": payer_name,
        "items": items,
        "preference_id": result["preference_id"],
        "init_point": result["init_point"],
        "total_amount": result["total_amount"],
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
    }

    file_path = output_dir / f"{order_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"💾 Payment link saved to {file_path}")
    return output_data


async def run_agent_with_order(order: dict):
    """
    Runs the Payment Link Generator Agent with an order dictionary.

    Args:
        order (dict): Dictionary containing order_id, payer_name, items, and optionally custom back URLs.

    Returns:
        dict: Payment link data including preference_id, init_point, total_amount, and status.
    """

    instructions = load_instructions("payment_link_generator")

    agent = Agent(
        name="Payment Link Generator",
        instructions=instructions,
        model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
        tools=[generate_payment_link],
    )

    items_str = "\n".join(
        f"- {item['title']} x{item['quantity']} (${item['unit_price']})"
        for item in order["items"]
    )

    prompt = f"""
    Generate a Mercado Pago link for order ID '{order['order_id']}' made by {order['payer_name']}.
    Items:
    {items_str}
    """

    result = await Runner.run(agent, prompt)
    return result

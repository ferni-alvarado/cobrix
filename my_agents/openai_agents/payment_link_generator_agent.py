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
from my_agents.openai_agents.tools.mercadopago_client import create_preference
from my_agents.utils.instructions import load_instructions

set_tracing_disabled(disabled=not TRACING_ENABLED)


def build_back_urls(success_url: str, failure_url: str, pending_url: str) -> dict:
    """
    Builds the back URLs for Mercado Pago preference creation.
    """
    return {
        "success": success_url or BACK_URLS["success"],
        "failure": failure_url or BACK_URLS["failure"],
        "pending": pending_url or BACK_URLS["pending"],
    }


def build_output_data(
    order_id: str, payer_name: str, items: list, preference: dict
) -> dict:
    """
    Builds the output data to be stored after creating a payment link.
    """
    return {
        "order_id": order_id,
        "payer_name": payer_name,
        "items": items,
        "preference_id": preference["preference_id"],
        "init_point": preference["init_point"],
        "total_amount": preference["total_amount"],
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
    }


def save_output_to_file(order_id: str, data: dict):
    """
    Saves the output data to a JSON file.
    """
    output_dir = Path("data/payment_links")
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"{order_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Payment link saved to {file_path}")


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
    back_urls = build_back_urls(success_url, failure_url, pending_url)
    preference = create_preference(items, back_urls)
    output_data = build_output_data(order_id, payer_name, items, preference)
    save_output_to_file(order_id, output_data)
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

    Use the following back URLs:
    - Success URL: {order.get('success_url', BACK_URLS['success'])}
    - Failure URL: {order.get('failure_url', BACK_URLS['failure'])}
    - Pending URL: {order.get('pending_url', BACK_URLS['pending'])}
    """

    result = await Runner.run(agent, prompt)
    return result

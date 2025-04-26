from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
    set_tracing_disabled,
)

from my_agents.config import MODEL_NAME, TRACING_ENABLED, client
from my_agents.openai_agents.mp.mercadopago_client import get_preference_by_id
from my_agents.utils.instructions import load_instructions

set_tracing_disabled(disabled=not TRACING_ENABLED)


@function_tool
def check_payment_status(preference_id: str) -> dict:
    """
    Given a Mercado Pago preference ID, returns its payment status.
    """
    return get_preference_by_id(preference_id)


async def run_agent_with_preference_id(preference_id: str):
    """
    Runs the Payment Status Checker Agent to verify the status of a payment via its preference ID.

    Args:
        preference_id (str): The Mercado Pago preference ID to check.

    Returns:
        dict: Payment status data including 'status', 'last_update', and 'preference_id'.
    """

    instructions = load_instructions("payment_status_instructions")

    agent = Agent(
        name="Payment Status Checker",
        instructions=instructions,
        model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
        tools=[check_payment_status],
    )

    test_preference_id = "182515349-d317f980-fd6a-441c-9cb6-e66966b619c7"

    prompt = f"Check the payment status for preference ID: {preference_id}"
    result = await Runner.run(agent, prompt)
    print(result.final_output)
    return result

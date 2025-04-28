import asyncio

from my_agents.openai_agents.payment_link_generator_agent import run_agent_with_order


async def run_test():
    print("🧪 Testing Payment Link Generator with custom order...")

    test_order = {
        "order_id": "ORD-TEST-99",
        "payer_name": "Fernando López",
        "items": [
            {
                "id": "prod-101",
                "title": "Empanadas x12",
                "quantity": 1,
                "unit_price": 4200.0,
            },
            {
                "id": "prod-102",
                "title": "Coca-Cola 1.5L",
                "quantity": 2,
                "unit_price": 1800.0,
            },
        ],
    }

    result = await run_agent_with_order(test_order)

    print("Result:", result)

    assert (
        "https://www.mercadopago.com" in result.final_output
    ), "Missing Mercado Pago link"
    print("✅ Test passed!")


if __name__ == "__main__":
    asyncio.run(run_test())

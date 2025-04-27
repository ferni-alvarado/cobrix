import asyncio

from my_agents.openai_agents.order_processing_agent import run_agent_with_order


async def run_test():
    print("🧪 Testing Order Processing Agent...\n")

    order = {
        "products_requested": [
            {"name": "Coca-Cola", "quantity": 2},
            {"name": "Empanada de carne", "quantity": 3},
            {"name": "helado 1/2 kilo", "quantity": 1},
        ],
        "ice_cream_flavors_requested": ["Chocolate", "Maracuyá"],
    }

    result = await run_agent_with_order(order)

    print("Order Processing Agent Result:", result)

    print("\n🎉 Test completed!")


if __name__ == "__main__":
    asyncio.run(run_test())

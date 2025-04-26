import asyncio

from my_agents.openai_agents.payment_status_agent import run_agent_with_preference_id


async def run_test():
    print("🧪 Testing Payment Status Checker with custom preference ID...")

    test_preference_id = "182515349-25235b34-7b34-4289-8c6d-0c3ebb29ee8c"
    result = await run_agent_with_preference_id(test_preference_id)
    assert "status" in result.final_output, "Missing payment status in the response"
    assert "last_update" in result.final_output, "Missing last update in the response"
    assert (
        "preference_id" in result.final_output
    ), "Missing preference ID in the response"
    print("✅ Test passed!")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(run_test())

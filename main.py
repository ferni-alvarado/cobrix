import asyncio
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

# This example demonstrates how to use the OpenAIChatCompletionClient with the AssistantAgent.  

# Setup the client to use GitHub Models
load_dotenv()

client = OpenAIChatCompletionClient(model="gpt-4o", api_key=os.environ["GITHUB_TOKEN"], base_url="https://models.inference.ai.azure.com")


agent = AssistantAgent(
    "spanish_tutor",
    model_client=client,
    system_message="You are a Spanish tutor. ONLY respond in Spanish.",
)


async def main() -> None:
    response = await agent.on_messages(
        [TextMessage(content="´how do you say 'i want to eat a big cheeseburger'?", source="user")],
        cancellation_token=CancellationToken(),
    )
    print(response.chat_message.content)


if __name__ == "__main__":
    asyncio.run(main())
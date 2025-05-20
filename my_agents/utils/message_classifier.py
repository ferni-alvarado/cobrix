import os
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import CancellationToken
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure client to use GitHub models
client = OpenAIChatCompletionClient(
    model="gpt-4o", 
    api_key=os.environ.get("GITHUB_TOKEN"), 
    base_url="https://models.inference.ai.azure.com"
)

# Create a classifier agent
classifier_agent = AssistantAgent(
    "classifier",
    model_client=client,
    system_message="""
    Your only job is to classify the intent of a message.
    
    You must determine if a message is:
    - "greeting": A greeting or introduction (e.g., "Hello", "Good morning")
    - "query": A question about products, prices, hours, etc.
    - "order": A message indicating intention to buy or order products
    - "other": Any other type of message
    
    You must respond ONLY with the type, without explanations or other text.
    For example: "greeting", "query", "order", or "other".
    """,
)

async def classify_intent(message: str) -> str:
    """
    Classify the intent of a message using an LLM agent.
    
    Args:
        message: The message to classify
        
    Returns:
        The detected intent: "greeting", "query", "order", or "other"
    """
    response = await classifier_agent.on_messages(
        [TextMessage(content=message, source="user")],
        cancellation_token=CancellationToken(),
    )
    
    # Clean the response to ensure we only have the classification
    intent = response.chat_message.content.strip().lower()
    
    # Validate that it's a valid classification
    valid_intents = ["greeting", "query", "order", "other"]
    if intent not in valid_intents:
        # If the response is not valid, use a fallback approach
        if "hello" in message.lower() or "hi" in message.lower() or "good" in message.lower():
            return "greeting"
        elif "?" in message or "how" in message.lower() or "what" in message.lower() or "time" in message.lower():
            return "query"
        elif "want" in message.lower() or "order" in message.lower() or "buy" in message.lower():
            return "order"
        else:
            return "other"
    
    return intent
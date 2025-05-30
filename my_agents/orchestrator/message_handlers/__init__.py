# my_agents/orchestrator/message_handlers/__init__.py

from abc import ABC, abstractmethod

from my_agents.core.config import MODEL_NAME, client
from my_agents.core.state_manager import StateManager


class BaseMessageHandler(ABC):
    """Base class for all message handlers"""

    def __init__(self):
        self.state_manager = StateManager.get_instance()

    @abstractmethod
    async def handle(self, message: str, user_id: str) -> str:
        """Handle the message and return response"""
        pass

    async def _call_llm(self, system_message: str, conversation_history: list) -> str:
        """Common method to call LLM with error handling"""
        try:
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": system_message}]
                + conversation_history,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return self._get_fallback_response()

    @abstractmethod
    def _get_fallback_response(self) -> str:
        """Return fallback response when LLM fails"""
        pass

from my_agents.utils.instructions import load_instructions

from . import BaseMessageHandler


class GreetingHandler(BaseMessageHandler):

    def __init__(self):
        super().__init__()
        self.system_message = load_instructions("system_message")

    async def handle(self, message: str, user_id: str) -> str:
        """Handle user greetings"""
        state = self.state_manager.get_state(user_id)
        return await self._call_llm(self.system_message, state["history"])

    def _get_fallback_response(self) -> str:
        return "¡Hola! ¿En qué puedo ayudarte hoy? 😊"

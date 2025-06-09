from dotenv import load_dotenv

from my_agents.core.state_manager import StateManager
from my_agents.utils.instructions import load_instructions

from .intent_classifier import IntentClassifier
from .message_handlers.greeting_handler import GreetingHandler
from .message_handlers.order_handler import OrderHandler
from .message_handlers.query_handler import QueryHandler

# Load environment variables
load_dotenv()


class OrchestratorAgent:
    def __init__(self):
        """
        Initialize the orchestrator agent, which acts as the central coordinator
        for all customer interactions and handles the flow between different specialized agents.
        """
        # Load system message
        try:
            self.system_message = load_instructions("orchestrator")
        except FileNotFoundError:
            self.system_message = self._get_default_system_message()

        # Initialize components
        self.state_manager = StateManager.get_instance()
        self.intent_classifier = IntentClassifier()

        # Initialize handlers
        self.handlers = {
            "greeting": GreetingHandler(),
            "query": QueryHandler(),
            "order": OrderHandler(),
        }

    async def handle_message(self, message: str, user_id: str) -> str:
        """
        Handle an incoming message and return the appropriate response

        Args:
            message: The text message received from the user
            user_id: Unique identifier for the user (phone number or ID)

        Returns:
            The response to send to the user
        """
        # Get user state
        state = self.state_manager.get_state(user_id)

        # Check for pending payment notifications
        # if state.get("should_notify_payment"):
        #    return self._handle_payment_notification(user_id, state) Lo podés eliminar si el notifier_loop se encarga 100% de notificar pagos

        # Save message in history
        state["history"].append({"role": "user", "content": message})

        # Classify message intent and get response
        intent = await self.intent_classifier.classify(message)
        response = await self._get_response_for_intent(intent, message, user_id)

        # Save response in history and update state
        state["history"].append({"role": "assistant", "content": response})
        self.state_manager.update_state(user_id, state)

        return response

    async def _get_response_for_intent(
        self, intent: str, message: str, user_id: str
    ) -> str:
        """Get response based on classified intent"""
        handler = self.handlers.get(intent)

        if handler:
            return await handler.handle(message, user_id)
        else:
            # Fallback to query handler for unknown intents
            return await self.handlers["query"].handle(message, user_id)

    def _handle_payment_notification(self, user_id: str, state: dict) -> str:
        """Handle pending payment notifications"""
        notification_message = state.get(
            "notification_message", "Tu pago ha sido procesado."
        )

        # Clear the notification
        state["should_notify_payment"] = False
        self.state_manager.update_state(user_id, state)

        return notification_message

    def _get_default_system_message(self) -> str:
        """Return default system message if file not found"""
        return load_instructions("system_message")

from my_agents.core.config import MODEL_NAME, client
from my_agents.utils.instructions import load_instructions


class IntentClassifier:
    def __init__(self):
        self.classification_prompt = load_instructions("intent_classification")

    async def classify(self, message: str) -> str:
        """
        Classify the intent of a user message

        Args:
            message: The message to classify

        Returns:
            The intent classification: "greeting", "query", "order", or "other"
        """
        try:
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.classification_prompt},
                    {"role": "user", "content": message},
                ],
                temperature=0.1,
                max_tokens=10,
            )

            intent = response.choices[0].message.content.strip().lower()

            # Validate that it's a valid classification
            valid_intents = ["greeting", "query", "order", "other"]
            if intent not in valid_intents:
                return self._fallback_classification(message)

            return intent

        except Exception as e:
            print(f"Error classifying intent: {e}")
            return self._fallback_classification(message)

    def _fallback_classification(self, message: str) -> str:
        """Fallback classification using simple rules"""
        message_lower = message.lower()

        greeting_words = ["hello", "hi", "good", "hola", "buenos", "buenas"]
        if any(word in message_lower for word in greeting_words):
            return "greeting"

        question_indicators = ["?"] + [
            "how",
            "what",
            "when",
            "where",
            "which",
            "who",
            "why",
            "cómo",
            "qué",
            "cuándo",
            "dónde",
            "cuál",
            "quién",
            "por qué",
        ]
        if any(indicator in message_lower for indicator in question_indicators):
            return "query"

        order_words = [
            "want",
            "order",
            "buy",
            "get",
            "quiero",
            "pedir",
            "comprar",
            "traer",
        ]
        if any(word in message_lower for word in order_words):
            return "order"

        return "other"

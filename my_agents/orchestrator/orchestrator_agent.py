import asyncio
import json
import os
import re
from typing import Dict, List, Optional

from dotenv import load_dotenv

from my_agents.openai_agents.order_processing_agent import run_agent_with_order
from my_agents.openai_agents.payment_link_generator_agent import (
    run_agent_with_order as generate_payment_link,
)
from my_agents.utils.instructions import load_instructions
# NUEVO: Importar el StateManager
from my_agents.utils.state_manager import StateManager

# Load environment variables
load_dotenv()

# Import the client from your config
from my_agents.config import MODEL_NAME, client


class OrchestratorAgent:
    def __init__(self):
        """
        Initialize the orchestrator agent, which acts as the central coordinator for all customer interactions
        and handles the flow between different specialized agents.
        """
        # Load orchestrator instructions if available, or use default
        try:
            self.system_message = load_instructions("orchestrator")
        except FileNotFoundError:
            self.system_message = """
            You are an intelligent orchestrator for the ordering system of Delicias Fueguinas,
            an ice cream shop/restaurant in Río Grande, Tierra del Fuego, Argentina.

            Your job is to receive messages, classify their intent, and manage the appropriate flow:

            1. If it's a greeting: Respond kindly and ask how you can help
            2. If it's a query: Respond directly using your knowledge
            3. If it's an order: Coordinate the complete process of verification, payment, and confirmation

            For orders, you must:
            - Extract products and quantities from the text
            - Verify availability (using the processing agent)
            - Handle out-of-stock situations by offering alternatives
            - Create orders and generate payment links when everything is verified

            Always maintain a friendly and personalized tone with the customer.

            About the business:
            - We are an ice cream shop/restaurant called "Delicias Fueguinas"
            - Located in Río Grande, Tierra del Fuego, Argentina
            - We offer artisanal ice cream, desserts, beverages, and fast food
            - Hours are from 10:00 AM to 10:00 PM every day
            - We deliver with an additional cost depending on the area

            Always respond in Spanish, using a friendly and approachable tone, as if you were
            an attentive and helpful employee of the business.
            """

        # NUEVO: Usar StateManager en lugar de conversation_state
        self.state_manager = StateManager.get_instance()
        # ELIMINAR: self.conversation_state = {}

    async def handle_message(self, message: str, user_id: str) -> str:
        """
        Handle an incoming message and return the appropriate response

        Args:
            message: The text message received from the user
            user_id: Unique identifier for the user (phone number or ID)

        Returns:
            The response to send to the user
        """
        # MODIFICADO: Obtener estado del StateManager
        state = self.state_manager.get_state(user_id)
        
        # NUEVO: Verificar notificaciones pendientes
        if state.get("should_notify_payment"):
            notification_message = state.get("notification_message", "Tu pago ha sido procesado.")
            # Limpiar la notificación para no mostrarla nuevamente
            state["should_notify_payment"] = False
            self.state_manager.update_state(user_id, state)
            return notification_message

        # Save message in history
        state["history"].append({"role": "user", "content": message})

        # Classify message intent
        intent = await self._classify_intent(message)

        # Process according to the intent
        if intent == "greeting":
            response = await self._handle_greeting(message, user_id)
        elif intent == "query":
            response = await self._handle_query(message, user_id)
        elif intent == "order":
            response = await self._handle_order(message, user_id)
        else:
            # Handle as a general query if unclear
            response = await self._handle_query(message, user_id)

        # Save response in history
        state["history"].append({"role": "assistant", "content": response})
        
        # NUEVO: Actualizar el estado
        self.state_manager.update_state(user_id, state)
        
        return response

    async def _classify_intent(self, message: str) -> str:
        """
        Classify the intent of a user message using the OpenAI API

        Args:
            message: The message to classify

        Returns:
            The intent classification: "greeting", "query", "order", or "other"
        """
        try:
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": """
                    Your only job is to classify the intent of a message.

                    You must determine if a message is:
                    - "greeting": A greeting or introduction (e.g., "Hello", "Good morning")
                    - "query": A question about products, prices, hours, etc.
                    - "order": A message indicating intention to buy or order products
                    - "other": Any other type of message

                    You must respond ONLY with the type, without explanations or other text.
                    For example: "greeting", "query", "order", or "other".
                    """,
                    },
                    {"role": "user", "content": message},
                ],
                temperature=0.1,
                max_tokens=10,
            )

            intent = response.choices[0].message.content.strip().lower()

            # Validate that it's a valid classification
            valid_intents = ["greeting", "query", "order", "other"]
            if intent not in valid_intents:
                # Fallback with simple rule-based classification
                if any(
                    word in message.lower()
                    for word in ["hello", "hi", "good", "hola", "buenos", "buenas"]
                ):
                    return "greeting"
                elif "?" in message or any(
                    word in message.lower()
                    for word in [
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
                ):
                    return "query"
                elif any(
                    word in message.lower()
                    for word in [
                        "want",
                        "order",
                        "buy",
                        "get",
                        "quiero",
                        "pedir",
                        "comprar",
                        "traer",
                    ]
                ):
                    return "order"
                else:
                    return "other"

            return intent

        except Exception as e:
            print(f"Error classifying intent: {e}")
            # Fallback to "other" if there's an error
            return "other"

    async def _handle_greeting(self, message: str, user_id: str = None) -> str:
        """Handle user greetings"""
        try:
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": message},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error handling greeting: {e}")
            return "¡Hola! ¿En qué puedo ayudarte hoy? 😊"

    async def _handle_query(self, message: str, user_id: str = None) -> str:
        """Handle general queries"""
        try:
            response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": message},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error handling query: {e}")
            return "Lo siento, no pude procesar tu consulta en este momento. ¿Podrías intentarlo de nuevo?"

    async def _handle_order(self, message: str, user_id: str) -> str:
        """Handle orders, verify stock and generate payment links"""
        # MODIFICADO: Obtener estado del StateManager
        state = self.state_manager.get_state(user_id)

        # If we're waiting for a response for alternatives
        if state["waiting_for_alternative"]:
            return await self._handle_alternative_response(message, user_id)

        # Extract order details using the assistant
        try:
            extraction_response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": """
                    Extract the products and quantities from the following order, and return it in structured JSON format:
                    {
                        "products_requested": [
                            {"name": "Product name", "quantity": quantity},
                            ...
                        ],
                        "ice_cream_flavors_requested": ["flavor1", "flavor2", ...]
                    }
                    Just return the JSON, nothing else.
                    """,
                    },
                    {
                        "role": "user",
                        "content": f"Extract the products and quantities from the following order: {message}",
                    },
                ],
                response_format={"type": "json_object"},
            )

            # Parse the JSON response
            order_json = extraction_response.choices[0].message.content
            print(f"Extracted order JSON: {order_json}")
            order = json.loads(order_json)
            print(f"Parsed order: {order}")
            # Verify availability with the processing agent
            processed_order = await run_agent_with_order(order)
            print(f"Processed order: {processed_order}")

            # Check if there are products out of stock
            if processed_order.get("not_found_products", []) or processed_order.get(
                "out_of_stock_products", []
            ):

                print(
                    f"Out of stock products: {processed_order.get('out_of_stock_products', [])}"
                )

                # Save pending order and mark that we're waiting for an alternative response
                state["pending_order"] = processed_order
                state["waiting_for_alternative"] = True
                
                # NUEVO: Actualizar el estado
                self.state_manager.update_state(user_id, state)

                # Build message offering alternatives
                not_found = processed_order.get("not_found_products", [])
                out_of_stock = processed_order.get("out_of_stock_products", [])
                alternatives_msg = self._build_alternatives_message(
                    out_of_stock, not_found
                )
                return alternatives_msg

            # If everything is in stock, generate payment link
            payment_data = {
                "order_id": processed_order["order_id"],
                "payer_name": "Cliente",  # Ideally extracted from message or history
                "items": self._convert_to_payment_items(
                    processed_order["validated_products"]
                ),
            }
            print(f"Payment data: {payment_data}")
            payment_link_result = await generate_payment_link(payment_data)
            print(f"Payment link result: {payment_link_result}")
            
            # NUEVO: Registrar el pedido en el StateManager
            if payment_link_result and "preference_id" in payment_link_result:
                # Guardar el pedido en el estado
                state["pending_order"] = payment_link_result
                
                # Registrar la asociación de IDs
                self.state_manager.register_order(
                    user_id=user_id,
                    order_id=payment_link_result["order_id"],
                    preference_id=payment_link_result["preference_id"]
                )
                
                # Actualizar el estado
                self.state_manager.update_state(user_id, state)

            # Build response with payment link
            response = (
                f"¡Gracias por tu pedido! Hemos confirmado todos los productos.\n\n"
                f"Datos: ${payment_link_result}\n"
                f"Una vez realizado el pago, te confirmaremos tu pedido."
            )

            return response

        except Exception as e:
            # Handle processing errors
            print(f"Error processing order: {e}")
            return "Lo siento, tuvimos un problema al procesar tu pedido. ¿Podrías intentarlo de nuevo?"

    async def _handle_alternative_response(self, message: str, user_id: str) -> str:
        """Handle customer response when alternatives are offered due to stock issues"""
        # MODIFICADO: Obtener estado del StateManager
        state = self.state_manager.get_state(user_id)

        try:
            print("Handling alternative response...")
            print(f"User message: {message}")

            # Clear the waiting for alternative flag regardless of what happens next
            state["waiting_for_alternative"] = False
            
            # NUEVO: Actualizar el estado temprano
            self.state_manager.update_state(user_id, state)

            # Keep the original order ID and validated products
            original_order_id = state["pending_order"]["order_id"]
            original_validated_products = state["pending_order"].get(
                "validated_products", []
            )

            print(f"Original order ID: {original_order_id}")
            print(f"Original validated products: {original_validated_products}")

            # Extract new products from the customer's response
            extraction_response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": """
                    Extract the products and quantities from the following order, and return it in structured JSON format:
                    {
                        "products_requested": [
                            {"name": "Product name", "quantity": quantity},
                            ...
                        ],
                        "ice_cream_flavors_requested": ["flavor1", "flavor2", ...]
                    }
                    Just return the JSON, nothing else.
                    """,
                    },
                    {
                        "role": "user",
                        "content": f"Extract the products and quantities from the following order: {message}",
                    },
                ],
                response_format={"type": "json_object"},
            )

            # Parse the JSON response
            order_json = extraction_response.choices[0].message.content
            print(f"Extracted additional products JSON: {order_json}")
            additional_order = json.loads(order_json)
            print(f"Parsed additional products: {additional_order}")

            # Process just the new products
            new_processed_order = await run_agent_with_order(additional_order)
            print(f"New processed order: {new_processed_order}")

            # Check if the new products have issues
            if new_processed_order.get(
                "not_found_products", []
            ) or new_processed_order.get("out_of_stock_products", []):
                # Still have issues with the new order - offer alternatives again
                state["pending_order"] = new_processed_order
                state["waiting_for_alternative"] = True

                # Build message offering alternatives
                not_found = new_processed_order.get("not_found_products", [])
                out_of_stock = new_processed_order.get("out_of_stock_products", [])
                alternatives_msg = self._build_alternatives_message(
                    out_of_stock, not_found
                )
                return alternatives_msg

            # Combine the original validated products with the new validated products
            combined_validated_products = (
                original_validated_products
                + new_processed_order.get("validated_products", [])
            )
            print(f"Combined validated products: {combined_validated_products}")

            # Calculate the combined total amount
            combined_total = sum(
                product.get("subtotal", 0) for product in combined_validated_products
            )

            # Generate payment link for the combined order
            payment_data = {
                "order_id": original_order_id,  # Keep the original order ID
                "payer_name": "Cliente",
                "items": self._convert_to_payment_items(combined_validated_products),
            }

            print(f"Payment data: {payment_data}")
            payment_link_result = await generate_payment_link(payment_data)
            print(f"Payment link result: {payment_link_result}")

            # Format the list of products for the response
            product_list = ""
            for product in combined_validated_products:
                product_list += f"- {product.get('name', 'Producto')}: ${product.get('subtotal', 0)}\n"

            response = (
                f"¡Perfecto! He actualizado tu pedido con los nuevos productos.\n\n"
                f"Tu pedido ahora incluye:\n{product_list}\n"
                f"Total a pagar: ${combined_total}\n"
                f"Link de pago: {payment_link_result['init_point']}\n\n"
                f"Una vez realizado el pago, te confirmaremos tu pedido."
            )

            # NUEVO: Registrar el pedido actualizado
            if payment_link_result and "preference_id" in payment_link_result:
                # Actualizar el pedido en el estado
                state["pending_order"] = payment_link_result
                
                # Actualizar la asociación de IDs
                self.state_manager.register_order(
                    user_id=user_id,
                    order_id=payment_link_result["order_id"],
                    preference_id=payment_link_result["preference_id"]
                )
                
                # Actualizar el estado
                self.state_manager.update_state(user_id, state)

            return response

        except Exception as e:
            import traceback

            print(f"Error handling alternative response: {e}")
            print(traceback.format_exc())
            return "Lo siento, hubo un problema al actualizar tu pedido. ¿Podrías intentarlo de nuevo?"

    def _build_alternatives_message(self, out_of_stock: List, not_found: List) -> str:
        """Build a message offering alternatives for out-of-stock or not found products"""
        message = "Lo siento, pero algunos productos no están disponibles en este momento:\n\n"

        # Process out of stock items
        for product in out_of_stock:
            if (
                isinstance(product, dict)
                and "product" in product
                and "available_stock" in product
            ):
                # Using dictionary format
                name = product["product"]
                available = product["available_stock"]

                if available > 0:
                    message += (
                        f"- {name}: Solo tenemos {available} unidades disponibles\n"
                    )
                else:
                    message += f"- {name}: No disponible por el momento\n"
            else:
                # Simple string format
                message += f"- {product}: No disponible por el momento\n"

        # Process not found items
        for product in not_found:
            if isinstance(product, dict) and "name" in product:
                product_name = product["name"]
            else:
                product_name = str(product)

            message += (
                f"- {product_name}: No encontramos este producto en nuestro menú\n"
            )

        message += "\n¿Te gustaría modificar tu pedido o elegir alguna de las alternativas sugeridas?"
        return message

    def _convert_to_payment_items(self, products: List) -> List[Dict]:
        """Convert verified products to the format expected by the payment link generator"""
        items = []
        for product in products:
            items.append(
                {
                    "title": product["name"],
                    "quantity": product["quantity"],
                    "unit_price": product["unit_price"],
                    "currency_id": "ARS",  # Assuming Argentine Pesos
                }
            )
        return items
from my_agents.core.state_manager import StateManager
from my_agents.openai_agents.order_processing_agent import run_agent_with_order
from my_agents.openai_agents.payment_link_generator_agent import (
    run_agent_with_order as generate_payment_link,
)

from ..order_processing.alternative_manager import AlternativeManager
from ..order_processing.order_extractor import OrderExtractor
from ..order_processing.payment_coordinator import PaymentCoordinator


class OrderHandler:
    def __init__(self):
        self.state_manager = StateManager.get_instance()
        self.order_extractor = OrderExtractor()
        self.alternative_manager = AlternativeManager()
        self.payment_coordinator = PaymentCoordinator()

    async def handle(self, message: str, user_id: str) -> str:
        """
        Main entry point for handling order-related messages
        This method is called by the orchestrator
        """
        return await self.handle_order(message, user_id)

    async def handle_order(self, message: str, user_id: str) -> str:
        """Handle order processing and coordination"""
        state = self.state_manager.get_state(user_id)

        # If we're waiting for a response for alternatives
        if state.get("waiting_for_alternative"):
            return await self._handle_alternative_response(message, user_id)

        # Extract order details
        order = await self.order_extractor.extract_products(message)

        # Verify availability
        processed_order = await run_agent_with_order(order)
        print(f"Processed order: {processed_order}")

        # Check for availability issues
        if self.alternative_manager.has_availability_issues(processed_order):
            return await self._handle_stock_issues(processed_order, user_id)

        # Generate payment link for available products
        return await self._generate_payment_link(processed_order, user_id)

    async def _handle_stock_issues(self, processed_order: dict, user_id: str) -> str:
        """Handle products that are out of stock or not found"""
        state = self.state_manager.get_state(user_id)

        # Save pending order and mark that we're waiting for alternative response
        state["pending_order"] = processed_order
        state["waiting_for_alternative"] = True
        self.state_manager.update_state(user_id, state)

        # Build message offering alternatives
        not_found = processed_order.get("not_found_products", [])
        out_of_stock = processed_order.get("out_of_stock_products", [])

        return self.alternative_manager.build_alternatives_message(
            out_of_stock, not_found
        )

    async def _generate_payment_link(self, processed_order: dict, user_id: str) -> str:
        """Generate payment link for validated products"""
        payment_data = {
            "order_id": processed_order["order_id"],
            "payer_name": "Cliente",
            "items": self.order_extractor.convert_to_payment_items(
                processed_order["validated_products"]
            ),
        }

        payment_link_result = await generate_payment_link(payment_data)

        # Register order in state manager
        if payment_link_result and "preference_id" in payment_link_result:
            state = self.state_manager.get_state(user_id)
            state["pending_order"] = payment_link_result

            self.state_manager.register_order(
                user_id=user_id,
                order_id=payment_link_result["order_id"],
                preference_id=payment_link_result["preference_id"],
            )

            self.state_manager.update_state(user_id, state)

        return self.payment_coordinator.build_payment_response(payment_link_result)

    async def _handle_alternative_response(self, message: str, user_id: str) -> str:
        """Handle customer response when alternatives are offered"""
        state = self.state_manager.get_state(user_id)

        try:
            # Clear the waiting flag
            state["waiting_for_alternative"] = False
            self.state_manager.update_state(user_id, state)

            # Keep original order data
            original_order_id = state["pending_order"]["order_id"]
            original_validated_products = state["pending_order"].get(
                "validated_products", []
            )

            # Extract and process new products
            additional_order = await self.order_extractor.extract_products(message)
            new_processed_order = await run_agent_with_order(additional_order)

            # Check if new products have issues
            if self.alternative_manager.has_availability_issues(new_processed_order):
                return await self._handle_stock_issues(new_processed_order, user_id)

            # Combine products and generate payment
            combined_products = self.alternative_manager.combine_validated_products(
                original_validated_products,
                new_processed_order.get("validated_products", []),
            )

            return await self._generate_combined_payment(
                original_order_id, combined_products, user_id
            )

        except Exception as e:
            print(f"Error handling alternative response: {e}")
            return "Lo siento, hubo un problema al actualizar tu pedido. ¿Podrías intentarlo de nuevo?"

    async def _generate_combined_payment(
        self, order_id: str, products: list, user_id: str
    ) -> str:
        """Generate payment for combined products"""
        payment_data = {
            "order_id": order_id,
            "payer_name": "Cliente",
            "items": self.order_extractor.convert_to_payment_items(products),
        }

        payment_link_result = await generate_payment_link(payment_data)

        # Update state
        if payment_link_result and "preference_id" in payment_link_result:
            state = self.state_manager.get_state(user_id)
            state["pending_order"] = payment_link_result

            self.state_manager.register_order(
                user_id=user_id,
                order_id=payment_link_result["order_id"],
                preference_id=payment_link_result["preference_id"],
            )

            self.state_manager.update_state(user_id, state)

        # Format response
        total = self.alternative_manager.calculate_total(products)
        product_list = self.alternative_manager.format_product_list(products)

        return (
            f"¡Perfecto! He actualizado tu pedido con los nuevos productos.\n\n"
            f"Tu pedido ahora incluye:\n{product_list}\n"
            f"Total a pagar: ${total}\n"
            f"Link de pago: {payment_link_result['init_point']}\n\n"
            f"Una vez realizado el pago, te confirmaremos tu pedido."
        )

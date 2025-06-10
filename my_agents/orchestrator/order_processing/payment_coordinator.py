from typing import Dict, Optional


class PaymentCoordinator:

    def build_payment_response(self, payment_link_result: Optional[Dict]) -> str:
        """Build response message with payment link information"""
        if not payment_link_result:
            return "Lo siento, tuvimos un problema al generar el link de pago. ¿Podrías intentarlo de nuevo?"

        return (
            f"¡Gracias por tu pedido! Hemos confirmado todos los productos.\n\n"
            f"Datos: ${payment_link_result}\n"
            f"Una vez realizado el pago, te confirmaremos tu pedido."
        )

    def build_payment_confirmation(self, order_details: Dict) -> str:
        """Build payment confirmation message"""
        return (
            f"¡Pago confirmado! Tu pedido está siendo preparado.\n"
            f"Número de pedido: {order_details.get('order_id', 'N/A')}\n"
            f"Te notificaremos cuando esté listo para retirar."
        )

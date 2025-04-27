import os

import mercadopago

from backend.services.websocket_manager import broadcast_payment_update

sdk = mercadopago.SDK(os.getenv("MERCADO_PAGO_ACCESS_TOKEN"))


async def process_webhook_event(payload: dict):
    payment_id = payload["data"]["id"]
    payment = sdk.payment().get(payment_id)["response"]

    status = payment.get("status")
    external_reference = payment.get("external_reference")
    payer_email = payment.get("payer", {}).get("email")
    total_amount = payment.get("transaction_amount")
    delivery_mode = (
        payment.get("additional_info", {})
        .get("shipment", {})
        .get("shipping_mode", "pickup")
    )

    await broadcast_payment_update(
        {
            "order_id": external_reference,
            "payment_status": status,
            "payer_email": payer_email,
            "delivery_mode": delivery_mode,
            "total_amount": total_amount,
        }
    )

import os

import mercadopago
from dotenv import load_dotenv

from backend.services.websocket_manager import broadcast_payment_update

load_dotenv()

access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")

if not access_token:
    raise EnvironmentError("MERCADO_PAGO_ACCESS_TOKEN is missing in .env file")

sdk = mercadopago.SDK(access_token)


def create_preference(items: list, back_urls: dict) -> dict:
    """
    Create a Mercado Pago preference link from a list of items and back URLs.

    Args:
        items (list): list of dicts, each with 'id', 'title', 'quantity', 'unit_price', and optionally 'currency_id'
        back_urls (dict): dict with 'success', 'failure', and 'pending' URLs

    Returns:
        dict: {'preference_id': str, 'init_point': str}
    """

    print("Creating Mercado Pago preference...", items, back_urls)

    preference_data = {
        "items": items,
        "back_urls": back_urls,
        "auto_return": "approved",
        "notification_url": "https://73b6-179-62-136-16.ngrok-free.app/webhook",
    }
    try:
        preference_response = sdk.preference().create(preference_data)
        response = preference_response.get("response", {})

        if "init_point" not in response:
            raise ValueError("'init_point' not found in Mercado Pago response.")

        return {
            "preference_id": response["id"],
            "init_point": response["init_point"],
            "total_amount": sum(
                item["unit_price"] * item["quantity"] for item in items
            ),
        }
    except Exception as e:
        raise RuntimeError(f"Error creating Mercado Pago preference: {e}")


def get_payment_status(preference_id: str) -> dict:
    """
    Get the status of a payment by preference ID.

    Returns:
        dict: {
            'status': 'approved' | 'pending' | 'rejected' | 'unknown',
            'payment_id': str,
            'preference_id': str,
            'last_update': str
        }
    """

    try:
        search_result = sdk.payment().search({"external_reference": preference_id})
        results = search_result.get("response", {}).get("results", [])

        if not results:
            return {
                "preference_id": preference_id,
                "status": "pending",
                "last_update": "unknown",
            }

        payment = results[0]
        return {
            "preference_id": preference_id,
            "payment_id": payment.get("id", "unknown"),
            "status": payment.get("status", "unknown"),
            "last_update": payment.get("date_last_updated", "unknown"),
        }
    except Exception as e:
        raise RuntimeError(f"Error retrieving payment status: {e}")


def search_preferences(filters: dict = {}) -> dict:
    """
    Search Mercado Pago preferences using optional filters.
    Only preferences created in the last 90 days will be returned.

    Args:
        filters (dict): Optional filters such as date_created_from, external_reference, etc.

    Returns:
        dict: Search results with preferences.
    """
    try:
        response = sdk.preference().search(filters)
        return response.get("response", {})
    except Exception as e:
        raise RuntimeError(f"Error searching Mercado Pago preferences: {e}")


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

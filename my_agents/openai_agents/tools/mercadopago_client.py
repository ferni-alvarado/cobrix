import os

import mercadopago
from dotenv import load_dotenv

load_dotenv()

access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")

if not access_token:
    raise EnvironmentError("MERCADO_PAGO_ACCESS_TOKEN is missing in .env file")

sdk = mercadopago.SDK(access_token)


def create_preference(items: list, back_urls: dict):
    """
    Create a Mercado Pago preference link from a list of items and back URLs.

    Args:
        items (list): list of dicts, each with 'id', 'title', 'quantity', 'unit_price', and optionally 'currency_id'
        back_urls (dict): dict with 'success', 'failure', and 'pending' URLs

    Returns:
        dict: {'preference_id': str, 'init_point': str}
    """

    preference_data = {
        "items": items,
        "back_urls": back_urls,
        "auto_return": "approved",
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


def get_preference_by_id(preference_id: str) -> dict:
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
        status = payment.get("status", "unknown")
        last_update = payment.get("date_last_updated", "unknown")
        payment_id = payment.get("id", "unknown")

        return {
            "preference_id": preference_id,
            "payment_id": payment_id,
            "status": status,
            "last_update": last_update,
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

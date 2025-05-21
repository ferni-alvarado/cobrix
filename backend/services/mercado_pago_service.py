import os

import mercadopago
from dotenv import load_dotenv

from backend.services.websocket_manager import broadcast_payment_update

load_dotenv()

# Configuración flexible de URLs para desarrollo y producción
# En producción, establecer la variable BASE_URL al dominio real de tu aplicación
# En desarrollo, puedes usar ngrok o una solución similar
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
NOTIFICATION_URL = f"{BASE_URL.rstrip('/')}{WEBHOOK_PATH}"

# Para modo desarrollo con ngrok, podemos usar una URL específica que sobrescriba la BASE_URL
NGROK_URL = os.getenv("NGROK_URL", None)
if NGROK_URL:
    NOTIFICATION_URL = f"{NGROK_URL.rstrip('/')}{WEBHOOK_PATH}"

print(f"Usando URL para notificaciones de Mercado Pago: {NOTIFICATION_URL}")

access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")
if not access_token:
    raise EnvironmentError("MERCADO_PAGO_ACCESS_TOKEN is missing in .env file")

sdk = mercadopago.SDK(access_token)


def create_preference(items: list, back_urls: dict, order_id: str) -> dict:
    """
    Create a Mercado Pago preference link from a list of items and back URLs.

    Args:
        order_id (str): Unique identifier for the order
        items (list): list of dicts, each with 'id', 'title', 'quantity', 'unit_price', and optionally 'currency_id'
        back_urls (dict): dict with 'success', 'failure', and 'pending' URLs

    Returns:
        dict: {'preference_id': str, 'init_point': str}
    """

    print("Creating Mercado Pago preference...", items, back_urls)

    preference_data = {
        "external_reference": order_id,
        "items": items,
        "back_urls": back_urls,
        "auto_return": "approved",
        "external_reference": order_id,
        "notification_url": NOTIFICATION_URL,
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
    """
    Process webhook events from Mercado Pago.
    Handles both payment and merchant_order notifications.

    Args:
        payload (dict): The webhook payload
    """
    try:
        print(f"Received webhook payload: {payload}")

        # Caso 1: Es una notificación de tipo "payment"
        if "data" in payload and "id" in payload.get("data", {}):
            payment_id = payload["data"]["id"]
            print(f"Procesando notificación de pago con ID: {payment_id}")

            payment_response = sdk.payment().get(payment_id)
            payment = payment_response["response"]

            status = payment.get("status")
            external_reference = payment.get("external_reference")
            total_amount = payment.get("transaction_amount")

            # Obtener información del pagador
            payer = payment.get("payer", {})
            payer_name = (
                f"{payer.get('first_name', '')} {payer.get('last_name', '')}".strip()
            )

            # Obtener número de teléfono si está disponible
            phone = payer.get("phone", {})
            area_code = phone.get("area_code", "")
            number = phone.get("number", "")
            full_phone_number = f"{area_code}{number}" if area_code and number else ""

            update_data = {
                "event": "payment_update",
                "notification_type": "payment",
                "payment_id": payment_id,
                "order_id": external_reference,
                "payment_status": status,
                "status": status,
                "total_amount": total_amount,
                "payer_name": payer_name,
                "payer_phone_number": full_phone_number,
            }

            print(f"Datos de pago procesados: {update_data}")
            await broadcast_payment_update(update_data)

        # Caso 2: Es una notificación de tipo "merchant_order"
        elif "topic" in payload and payload.get("topic") == "merchant_order":
            merchant_resource = payload.get("resource")

            update_data = {
                "event": "payment_update",
                "notification_type": "merchant_order",
                "url": merchant_resource,
            }

            await broadcast_payment_update(update_data)

        # Caso 3: Otro tipo de notificación
        else:
            print(f"Formato de notificación desconocido: {payload}")
            # Simplemente registramos y no causamos error
            await broadcast_payment_update(
                {"notification_type": "unknown", "raw_data": str(payload)}
            )

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Error procesando webhook: {str(e)}")
        # Enviar notificación de error pero no interrumpir el flujo
        await broadcast_payment_update(
            {
                "notification_type": "error",
                "error_message": str(e),
                "payload": str(payload),
            }
        )

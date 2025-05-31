import os

import mercadopago
from dotenv import load_dotenv

from backend.services.websocket_manager import broadcast_payment_update

load_dotenv()

BASE_URL = "https://fb23-179-62-95-234.ngrok-free.app"
NOTIFICATION_URL = f"{BASE_URL.rstrip('/')}/webhook"
access_token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")

if not access_token:
    raise EnvironmentError("MERCADO_PAGO_ACCESS_TOKEN is missing in .env file")

sdk = mercadopago.SDK(access_token)


def create_preference(items: list, back_urls: dict, order_id: str) -> dict:
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
    try:
        print(f"Received webhook payload: {payload}")

        # Caso 1: Es una notificación de tipo "payment"
        if "data" in payload and "id" in payload.get("data", {}):
            payment_id = payload["data"]["id"]
            print(f"Procesando notificación de pago con ID: {payment_id}")

            payment_response = sdk.payment().get(payment_id)
            payment = payment_response["response"]
            print(f"🔍 Respuesta completa del pago: {payment}")

            status = payment.get("status")
            external_reference = payment.get("external_reference")
            payer_email = payment.get("payer", {}).get("email")
            total_amount = payment.get("transaction_amount")

            update_data = {
                "notification_type": "payment",
                "payment_id": payment_id,
                "order_id": external_reference,
                "payment_status": status,
                "payer_email": payer_email,
                "total_amount": total_amount,
            }

            print(f"Datos de pago procesados: {update_data}")
            # NUEVO: Actualizar el estado en el StateManager
            if external_reference and status:
                from my_agents.utils.state_manager import StateManager
                
                state_manager = StateManager.get_instance()
                
                # Buscar preference_id a partir del order_id
                print(f"🔍 Buscando preference_id para order_id: {external_reference}")
                for pref_id, user_id in state_manager._preference_mapping.items():
                    user_state = state_manager.get_state(user_id)
                    if user_state.get("pending_order") and user_state["pending_order"].get("order_id") == external_reference:
                        preference_id = user_state["pending_order"].get("preference_id")
                        print(f"🔍 Encontrado preference_id: {preference_id} para order_id: {external_reference}")
                        
                        # Actualizar el estado del pago
                        success = state_manager.update_payment_status(
                            preference_id, 
                            status,
                            {
                                "payment_id": payment_id,
                                "payer_email": payer_email,
                                "total_amount": total_amount
                            }
                        )
                        print(f"🔍 Resultado detallado de update_payment_status: {success}")
                        if success:
                            print(f"✅ Estado actualizado para orden: {external_reference}, status: {status}")
                        else:
                            print(f"⚠️ No se pudo actualizar el estado para orden: {external_reference}")
                        
                        break

            await broadcast_payment_update(update_data)

        # Caso 2: Es una notificación de tipo "merchant_order"
        elif "topic" in payload and payload.get("topic") == "merchant_order":
            merchant_order_id = payload.get("id")
            print(
                f"Procesando notificación de orden comercial con ID: {merchant_order_id}"
            )

            # Obtener detalles de la orden
            merchant_response = sdk.merchant_order().get(merchant_order_id)
            merchant_order = merchant_response["response"]

            status = merchant_order.get("order_status")
            external_reference = merchant_order.get("external_reference")
            total_amount = merchant_order.get("total_amount")

            update_data = {
                "notification_type": "merchant_order",
                "merchant_order_id": merchant_order_id,
                "order_id": external_reference,
                "order_status": status,
                "total_amount": total_amount,
            }

            print(f"Datos de orden comercial procesados: {update_data}")
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

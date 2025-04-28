import os

import mercadopago
from dotenv import load_dotenv

load_dotenv()

# En modo de desarrollo, podemos habilitar un modo simulado
# para no depender de las API reales
MOCK_MODE = os.getenv("MOCK_MERCADOPAGO", "False").lower() == "true"

# Solo cargar token y SDK si no estamos en modo simulado
if not MOCK_MODE:
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
    if MOCK_MODE:
        # Modo simulación para desarrollo y testing
        import uuid
        
        total_amount = sum(item["unit_price"] * item["quantity"] for item in items)
        preference_id = f"MOCK_PREF_{uuid.uuid4().hex[:8]}"
        
        # URL simulada para pruebas
        init_point = f"https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id={preference_id}"
        
        print(f"[MOCK MODE] Creando preferencia simulada: {preference_id}")
        print(f"[MOCK MODE] Total: ${total_amount}")
        
        return {
            "preference_id": preference_id,
            "init_point": init_point,
            "total_amount": total_amount
        }
    else:
        # Modo real usando la API de Mercado Pago
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
    if MOCK_MODE or preference_id.startswith("MOCK_"):
        # En modo simulación, devolvemos un estado ficticio
        from datetime import datetime
        
        print(f"[MOCK MODE] Consultando estado de preferencia simulada: {preference_id}")
        
        return {
            "preference_id": preference_id,
            "payment_id": f"MOCK_PAYMENT_{preference_id[-6:]}",
            "status": "pending",
            "last_update": datetime.now().isoformat()
        }
    else:
        # Modo real usando la API de Mercado Pago
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
    if MOCK_MODE:
        # En modo simulación, devolvemos resultados ficticios
        print(f"[MOCK MODE] Buscando preferencias con filtros: {filters}")
        return {"results": [], "paging": {"total": 0, "limit": 10, "offset": 0}}
    else:
        # Modo real usando la API de Mercado Pago
        try:
            response = sdk.preference().search(filters)
            return response.get("response", {})
        except Exception as e:
            raise RuntimeError(f"Error searching Mercado Pago preferences: {e}")
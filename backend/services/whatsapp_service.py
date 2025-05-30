# cliente para enviar mensajes usando la API de WhatsApp.

import os

import httpx

WHATSAPP_API_URL = "https://graph.facebook.com/v19.0"
PHONE_NUMBER_ID = "703805576141331"
ACCESS_TOKEN = os.getenv("META_TEMP_TOKEN")  # Guardalo en .env y cargalo con dotenv


async def send_whatsapp_message(phone_number: str, template_name: str = "hello_world"):
    url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {"name": template_name, "language": {"code": "en_US"}},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        print("Respuesta de WhatsApp:", response.status_code, response.text)
        return response.json()

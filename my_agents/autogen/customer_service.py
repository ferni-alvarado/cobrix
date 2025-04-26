import asyncio
import os
import json
from typing import Dict, List, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from autogen_core import CancellationToken
from my_agents.utils.order_models import OrderType

# Cargar variables de entorno
load_dotenv()

# Configurar cliente para usar modelos de GitHub
client = OpenAIChatCompletionClient(
    model="gpt-4o", 
    api_key=os.environ["GITHUB_TOKEN"], 
    base_url="https://models.inference.ai.azure.com"
)

# Función para convertir el pedido en lenguaje natural a formato estructurado
def extract_order(text: str) -> Dict:
    """
    Esta función se llamará desde el agente de atención al cliente
    para extraer los detalles del pedido del texto en lenguaje natural.
    """
    # En una implementación real, esto se haría con NLP
    # Aquí simulamos la extracción
    return {
        "productos_pedidos": [],
        "sabores_helado": []
    }

# Crear el agente de atención al cliente
customer_service_agent = AssistantAgent(
    "atencion_cliente",
    model_client=client,
    system_message="""
    Eres un amable agente de atención al cliente para una heladería/restaurante.
    Tu trabajo es:
    
    1. Saludar al cliente por su nombre (si lo conoces)
    2. Recordar sus preferencias de pedidos anteriores
    3. Tomar su pedido en lenguaje natural
    4. Convertir el pedido a un formato estructurado para ser procesado
    5. Mantener un tono amigable y personalizado
    6. Confirmar los detalles del pedido
    
    En caso de que pidan un helado, deben especificar los sabores, si no los especifican, pregunta por ellos.
    
    """,
    output_content_type=OrderType,
)


async def main() -> None:
    # Iniciar la conversación
    response = await customer_service_agent.on_messages(
        [
            TextMessage(content="Hola, soy Carlos. Quiero pedir 2 Coca-Cola, 3 empanadas de carne y un helado de medio kilo", source="user")
        ],
        cancellation_token=CancellationToken(),
    )
    print(response)
    json_response = response.chat_message.content.model_dump_json()
    print(json_response)


if __name__ == "__main__":
    asyncio.run(main())
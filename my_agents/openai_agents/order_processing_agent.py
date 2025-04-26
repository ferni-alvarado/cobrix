import asyncio
import os

from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel, Runner
from my_agents.utils.orders_tools import verificar_pedido, verificar_sabores_helado
import openai

load_dotenv()

client = openai.AsyncOpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ["GITHUB_TOKEN"],
)

model = OpenAIChatCompletionsModel(
    openai_client=client,
    model="gpt-4o",
)

agent = Agent(
    name="procesador_pedidos",
    model=model,
    instructions="""
Sos un agente encargado de procesar pedidos. Tu tarea incluye:

- Validar si hay stock y calcular precios de productos'.
- Cuando te pidan un helado, deberás verificar el tipo y precio de helado (1/4kg, 1/2kg, 1kg, cono, etc.) 
Verificar si los sabores de helado solicitados están disponibles'.

Recibirás pedidos en texto natural o en formato estructurado. Usá las herramientas disponibles cuando sea necesario.
""",
    tools=[verificar_pedido, verificar_sabores_helado] 
)

async def main() -> None:
    pedido = {
    "productos_pedidos": [
        {"nombre": "Coca-Cola", "cantidad": 2},
        {"nombre": "Empanada de carne", "cantidad": 3},
        {"nombre": "helado 1/2 kilo", "cantidad": 1},
    ],
    "sabores_helado": ["Chocolate", "Maracuyá"]
    }

    result = await Runner.run(agent, input=str(pedido))
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
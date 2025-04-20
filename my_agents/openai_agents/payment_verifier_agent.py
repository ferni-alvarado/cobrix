import asyncio
import glob
import json
from pathlib import Path

import easyocr
from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from agents.tool import function_tool

from my_agents.config import MODEL_NAME, TRACING_ENABLED, client

# Disable tracing since we're not connected to a supported tracing provider
set_tracing_disabled(disabled=not TRACING_ENABLED)

# Path to the instructions file
INSTRUCTIONS_PATH = (
    Path(__file__).parent.parent / "prompts" / "payment_verifier_instructions.md"
)


# Function to load instructions from file
def load_instructions():
    with open(INSTRUCTIONS_PATH, "r", encoding="utf-8") as file:
        instructions = file.read()
        return instructions


def _extract_text_from_image(image_path: str):
    reader = easyocr.Reader(["es"], gpu=False)
    results = reader.readtext(image_path)

    extracted_text = " ".join([text for _, text, _ in results])

    return {
        "extracted_text": extracted_text,
        "confidence_scores": [float(prob) for _, _, prob in results],
        "text_elements": [text for _, text, _ in results],
    }


@function_tool
def extract_text_from_image(image_path: str):
    return _extract_text_from_image(image_path)


@function_tool
def analyze_payment_receipt(text: str):
    pass


async def process_receipt(image_path, agent):
    print(f"Procesando imagen: {image_path}")

    # First we extract the text with our tool
    # Note: in this first implementation we call the function directly instead of using the agent
    ocr_result = _extract_text_from_image(image_path)

    prompt = f"""I have extracted the following text from a payment receipt image. Please analyze it and provide a detailed verification of the payment receipt: {ocr_result['extracted_text']}"""

    # Run the agent with the tools available
    result = await Runner.run(agent, prompt)

    return {
        "image_path": image_path,
        "ocr_text": ocr_result,
        "analysis": result.final_output,
    }


async def main():
    # Load instructions
    instructions = load_instructions()
    if not instructions:
        raise ValueError("Instructions file is empty or not found.")

    # Initialize the agent
    agent = Agent(
        name="Payment Verifier Assistant",
        instructions=instructions,
        model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
        tools=[
            extract_text_from_image,
            analyze_payment_receipt,
        ],
    )

    # Get all receipt images
    receipt_images = (
        glob.glob("data/receipts/*.jpeg")
        + glob.glob("data/receipts/*.jpg")
        + glob.glob("data/receipts/*.png")
    )

    if not receipt_images:
        print("No receipt images found in the specified directory.")
        return

    # Process each receipt
    results = []
    for image_path in receipt_images:
        result = await process_receipt(image_path, agent)
        results.append(result)

    # Save results to a JSON file
    output_dir = Path("data/results")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "verification_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())

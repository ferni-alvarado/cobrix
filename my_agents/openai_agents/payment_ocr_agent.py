import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

import easyocr
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
    set_tracing_disabled,
)

from my_agents.config import MODEL_NAME, TRACING_ENABLED, client
from my_agents.utils.instructions import load_instructions

set_tracing_disabled(disabled=not TRACING_ENABLED)


# Internal OCR function (not exposed to the agent)
def _extract_text_from_image(image_path: str):
    reader = easyocr.Reader(["es"], gpu=False)
    results = reader.readtext(image_path)
    return " ".join([text for _, text, _ in results])


# Tool 1 - OCR
@function_tool
def extract_text_from_image(image_path: str) -> dict:
    """
    Extracts raw text from a payment receipt image using OCR.
    Returns the raw text to be analyzed later.
    """
    text = _extract_text_from_image(image_path)
    return {"text": text}


# Tool 2 - Text analysis
@function_tool
def analyze_payment_receipt(text: str) -> dict:
    """
    Given the raw text extracted from a payment receipt, analyzes and returns structured payment information.
    """
    return {
        "status": "pending",
        "reason": "Tool placeholder. Implemented by the agent using the language model.",
    }


def extract_json_from_response(response: str) -> dict:
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON from agent response"}
    return {"error": "No JSON found in agent response"}


async def run_agent_with_receipt():
    """
    Runs the Payment OCR Agent to extract and analyze data from a payment receipt (image or PDF).

    This agent uses OCR to extract text and detect key fields like payer name, amount, and transaction ID.
    Returns structured data or flags inconsistencies for human review.
    """

    instructions = load_instructions("payment_ocr")

    agent = Agent(
        name="Payment Verifier",
        instructions=instructions,
        model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
        tools=[extract_text_from_image, analyze_payment_receipt],
    )

    # Get all receipt images
    receipts_dir = Path("data/receipts")
    receipt_images = (
        list(receipts_dir.glob("*.jpg"))
        + list(receipts_dir.glob("*.jpeg"))
        + list(receipts_dir.glob("*.png"))
    )

    if not receipt_images:
        print("No receipt images found.")
        return

    # Process each receipt
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(f"data/results/{today_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    for image_path in receipt_images:
        print(f"Processing {image_path}...")
        prompt = f"Please, analyze the payment receipt in the image: {str(image_path)}"
        result = await Runner.run(agent, prompt)

        receipt_id = Path(image_path).stem  # file name without extension
        parsed_json = extract_json_from_response(result.final_output)

        output_data = {
            "receipt_id": receipt_id,
            "image_path": str(image_path),
            "structured_data": parsed_json,
            "raw_response": result.final_output,
        }

        output_file = output_dir / f"receipt_result_{receipt_id}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        print(f"✅ Saved: {output_file}")

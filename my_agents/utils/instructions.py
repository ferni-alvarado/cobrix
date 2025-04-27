from pathlib import Path


def load_instructions(agent_filename: str) -> str:
    """
    Given the filename (without extension) of the prompt, loads it from the prompts folder.
    Example: load_instructions("payment_link_generator") → loads 'prompts/payment_link_generator_instructions.md'
    """
    prompts_dir = Path(__file__).parent.parent / "prompts"
    instructions_path = prompts_dir / f"{agent_filename}_instructions.md"

    if not instructions_path.exists():
        raise FileNotFoundError(f"Prompt not found: {instructions_path}")

    with open(instructions_path, "r", encoding="utf-8") as file:
        return file.read()

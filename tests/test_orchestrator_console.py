import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Get the absolute path of the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the parent directory to Python's path
project_root = os.path.dirname(script_dir)  # If test is in a subdirectory
# OR
project_root = script_dir  # If test is in the root directory

# Add to Python path
sys.path.append(project_root)

# Create necessary directories if they don't exist
os.makedirs(os.path.join(project_root, "data", "orders"), exist_ok=True)
os.makedirs(os.path.join(project_root, "data", "payment_links"), exist_ok=True)
os.makedirs(os.path.join(project_root, "data", "receipts"), exist_ok=True)

from dotenv import load_dotenv

from my_agents.orchestrator.orchestrator_agent import OrchestratorAgent


# Console formatting configuration
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GREY = "\033[90m"


def print_header():
    """Print the simulator header"""
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{Colors.CYAN}=" * 70)
    print(f"🤖 COBRIX - WHATSAPP CHAT SIMULATOR 🤖".center(70))
    print(f"=" * 70)
    print(f"📱 AI agent system for automating orders and payment verification")
    print(f"📝 Press Ctrl+C to exit | Type 'help' for commands{Colors.RESET}")
    print()


def print_message(role, message, timestamp=None):
    """Print a message formatted according to role"""
    timestamp = timestamp or datetime.now().strftime("%H:%M:%S")

    if role == "user":
        print(
            f"\n{Colors.GREY}[{timestamp}] {Colors.GREEN}🧑 User:{Colors.RESET} {message}"
        )
    elif role == "assistant":
        print(
            f"\n{Colors.GREY}[{timestamp}] {Colors.BLUE}🤖 Assistant:{Colors.RESET} {message}"
        )
    elif role == "system":
        print(
            f"\n{Colors.GREY}[{timestamp}] {Colors.YELLOW}⚙️ System:{Colors.RESET} {message}"
        )
    elif role == "error":
        print(
            f"\n{Colors.GREY}[{timestamp}] {Colors.RED}❌ Error:{Colors.RESET} {message}"
        )


def print_help():
    """Print available commands"""
    print(f"\n{Colors.YELLOW}Available commands:{Colors.RESET}")
    print("  - help: Show this list of commands")
    print("  - clear: Clear the screen")
    print("  - new: Start a new conversation")
    print("  - exit: Exit the program")
    print("  - debug: Toggle debug information")
    print("  - status: Show current conversation status")


async def run_console_chat():
    """
    Function to test the orchestrator through a console conversation.
    Simulates WhatsApp communication.
    """
    print_header()

    # Load environment variables
    load_dotenv()

    # Create an instance of the orchestrator
    print_message("system", "Initializing orchestrator agent...")
    orchestrator = OrchestratorAgent()

    # Generate test user ID (simulating a phone number)
    user_id = "whatsapp_+5492964123456"  # Simulates a Río Grande, TDF number
    debug_mode = False

    # Welcome message
    print_message("system", "Orchestrator ready! You can start chatting.")
    print_message(
        "system",
        "Simulate being a customer by writing messages as you would on WhatsApp.",
    )

    # Conversation loop
    while True:
        try:
            # Read user message
            user_input = input(f"\n{Colors.GREEN}🧑 Message:{Colors.RESET} ")

            # Process special commands
            if user_input.lower() in ["exit", "quit"]:
                print_message("system", "Ending chat. Goodbye!")
                break

            elif user_input.lower() == "help":
                print_help()
                continue

            elif user_input.lower() == "clear":
                print_header()
                continue

            elif user_input.lower() == "new":
                # Restart conversation with new ID
                user_id = f"whatsapp_+5492964{100000 + int(datetime.now().timestamp()) % 900000}"
                print_message("system", f"New conversation started with ID: {user_id}")
                continue

            elif user_input.lower() == "debug":
                debug_mode = not debug_mode
                print_message(
                    "system", f"Debug mode: {'enabled' if debug_mode else 'disabled'}"
                )
                continue

            elif user_input.lower() == "status":
                # Show current conversation status
                if user_id in orchestrator.conversation_state:
                    state = orchestrator.conversation_state[user_id]
                    print_message("system", f"Current status: {state['context']}")
                    print_message(
                        "system",
                        f"Waiting for alternative: {state['waiting_for_alternative']}",
                    )
                    if state["pending_order"]:
                        print_message(
                            "system",
                            f"Pending order: {state['pending_order']['order_id']}",
                        )
                else:
                    print_message("system", "No active conversation.")
                continue

            # If it's an empty message, ignore
            if not user_input.strip():
                continue

            # Log user message
            print_message("user", user_input)

            # Process message with the orchestrator
            print_message("system", "Processing message...")

            # Measure response time
            start_time = datetime.now()
            response = await orchestrator.handle_message(user_input, user_id)
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            # Show processing time in debug mode
            if debug_mode:
                print_message(
                    "system", f"Processing time: {processing_time:.2f} seconds"
                )

            # Show response
            print_message("assistant", response)

        except KeyboardInterrupt:
            print_message("system", "\nEnding chat. Goodbye!")
            break
        except Exception as e:
            print_message("error", f"Unexpected error: {str(e)}")
            if debug_mode:
                import traceback

                traceback.print_exc()


if __name__ == "__main__":
    try:
        # Run the async function
        asyncio.run(run_console_chat())
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
    except Exception as e:
        print(f"\n\nFatal error: {e}")

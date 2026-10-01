import os
from dotenv import load_dotenv

# Load variables from the .env file in the project root
load_dotenv()

from src.models import AgentRegistry
from src.agent.interpreter_agent import InterpreterAgent
from src.agent.rebooking_agent import BookingAgent
from src.orchestrator import Orchestrator

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Ensure it is defined in your .env file.")

    interpreter = InterpreterAgent("src/instruction/interpreter_prompt.txt")
    booking = BookingAgent("src/instruction/rebooking_prompt.txt")

    # 2. Bundle them in your AgentRegistry
    registry = AgentRegistry(
        InterpretorAgent=interpreter,
        BookingAgent=booking
    )

    # 3. Pass the registry to your Orchestrator
    orchestrator = Orchestrator(registry=registry)

    # 3. Test execution
    query = "Snowstorm grounded flight. PNR: SKY890. Please rebook me for 2026-10-02."
    response = orchestrator.decision(query)
    print(response)

if __name__ == "__main__":
    main()
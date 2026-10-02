import os
from dotenv import load_dotenv

load_dotenv()

from src.models import AgentRegistry
from src.agent.interpreter_agent import InterpreterAgent
from src.agent.rebooking_agent import BookingAgent
from src.orchestrator import Orchestrator

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY not found or default. Ensure your actual key is set in .env file.")

    interpreter = InterpreterAgent("src/instructions/interpreter_agent_prompt.txt")
    booking = BookingAgent("src/instructions/rebooking_agent_prompt.txt")

    # 2. Bundle them in your AgentRegistry
    registry = AgentRegistry(
        InterpretorAgent=interpreter,
        BookingAgent=booking
    )

    # 3. Pass the registry to your Orchestrator
    orchestrator = Orchestrator(registry=registry)

    # 4. Test execution
    query = "Snowstorm grounded flight. PNR: SKY890. Please rebook me for 2026-10-02."
    response = orchestrator.decision(query)
    print(response)

if __name__ == "__main__":
    main()
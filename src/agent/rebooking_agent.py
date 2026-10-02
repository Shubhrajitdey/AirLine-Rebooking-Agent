from typing import Any, Dict
import os
from google import genai

class BookingAgent:
    def __init__(self, prompt_path: str, api_token: str = None):
        self.agent_id = "agent:booking"
        with open(prompt_path, "r") as f:
            self.template = f.read()

        token = api_token or os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=token)
        self.model = "gemini-2.5-flash"

    def invoke(self, variables: Dict[str, Any]) -> str:
        prompt = self.template.format(
            pnr = variables.get("pnr") or variables.get("PNR", "UNKNOWN"),
            disruption_code = variables.get("disruption_code", "UNSPECIFIED"),
            waiver_applicable = "TRUE" if variables.get("waiver_applicable") else "FALSE",
            waiver_applicable_bool = "true" if variables.get("waiver_applicable") else "false",
            available_flight = variables.get("available_flight") or variables.get("available_flights") or "NONE",
            departure_time = variables.get("departure_time", "NONE")
        )
        response = self.client.models.generate_content(
            model = self.model,
            contents=prompt
        )
        return response.text
        
        
        

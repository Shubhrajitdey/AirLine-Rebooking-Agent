# Interpreter Agent
import os
from google import genai

class InterpreterAgent:
    def __init__(self, prompt_path: str, api_token: str = None):
        self.agent_id = "agent:interpreter"
        with open(prompt_path, "r") as f:
            self.template = f.read()

        token = api_token or os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=token)
        self.model = "gemini-2.5-flash"

    def invoke(self, user_query: str) -> str:
        prompt = self.template.format(user_query=user_query)
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )
        return response.text
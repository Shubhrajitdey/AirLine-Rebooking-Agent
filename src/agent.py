import json
import logging
from typing import Optional, List, Dict, Any

from src.config import GEMINI_API_KEY, GEMINI_MODEL
from src.prompts import AIRLINE_AGENT_SYSTEM_PROMPT
from src.tools import TOOLS

logger = logging.getLogger(__name__)

class AirlineAgent:
    """Conversational Rebooking Agent powered by Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model or GEMINI_MODEL
        self.client = None
        self.chat = None
        self.is_mock_mode = False

        self._initialize_gemini()

    def _initialize_gemini(self) -> None:
        """Initialize the Gemini client and chat session with tools."""
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("No valid GEMINI_API_KEY found. Operating in MOCK DEMO mode.")
            self.is_mock_mode = True
            return

        try:
            from google import genai
            from google.genai import types

            self.client = genai.Client(api_key=self.api_key)
            
            # Create a multi-turn chat session with system instruction and tool definitions
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=AIRLINE_AGENT_SYSTEM_PROMPT,
                    tools=TOOLS,
                    temperature=0.2,
                )
            )
            logger.info(f"Gemini client successfully initialized with model '{self.model_name}'.")
        except ImportError:
            # Fallback to google.generativeai if google-genai is not yet installed
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                model = legacy_genai.GenerativeModel(
                    model_name=self.model_name,
                    tools=TOOLS,
                    system_instruction=AIRLINE_AGENT_SYSTEM_PROMPT
                )
                self.chat = model.start_chat(enable_automatic_function_calling=True)
                logger.info(f"Initialized using legacy google-generativeai with model '{self.model_name}'.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini SDK: {e}. Falling back to mock mode.")
                self.is_mock_mode = True
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {e}. Falling back to mock mode.")
            self.is_mock_mode = True

    def send_message(self, user_message: str) -> str:
        """Send a message to the agent and receive the response.
        
        Handles automatic tool calling execution through Gemini SDK.
        """
        if self.is_mock_mode:
            return self._mock_respond(user_message)

        try:
            response = self.chat.send_message(user_message)
            return response.text
        except Exception as e:
            logger.error(f"Error communicating with Gemini: {e}")
            return f"I apologize, but I encountered an error communicating with our services: {str(e)}"

    def _mock_respond(self, user_message: str) -> str:
        """Simulated response for demonstration when GEMINI_API_KEY is not yet configured."""
        msg_lower = user_message.lower()
        if "sky101" in msg_lower or "doe" in msg_lower:
            from src.tools import get_booking_details, check_rebooking_policy, search_flights
            details = get_booking_details("SKY101", "Doe")
            policy = check_rebooking_policy("SKY101")
            flights = search_flights("SFO", "JFK", "2026-10-02")
            return (
                f"[MOCK AGENT NOTICE: Configure GEMINI_API_KEY in .env for live LLM reasoning]\n\n"
                f"Hello Mr. Doe, I see that your flight SK-402 from SFO to JFK was cancelled due to severe weather. "
                f"As a valued Platinum member, you are eligible for complimentary rebooking and meal vouchers.\n\n"
                f"Available alternative direct flights today:\n"
                f"1. Flight SK-404: Departs SFO 11:30 AM -> Arrives JFK 8:00 PM (Seats: 8 Economy, 2 Business)\n"
                f"2. Flight SK-406: Departs SFO 4:00 PM -> Arrives JFK 12:30 AM (Seats: 14 Economy)\n\n"
                f"Which flight would you prefer, and do you prefer a window or aisle seat?"
            )
        elif "sk-404" in msg_lower or "first" in msg_lower:
            from src.tools import rebook_flight, issue_voucher
            result = rebook_flight("SKY101", "SK-404", "Window")
            voucher = issue_voucher("SKY101", "MEAL")
            return (
                f"[MOCK AGENT NOTICE: Configure GEMINI_API_KEY in .env for live LLM reasoning]\n\n"
                f"You have been successfully rebooked onto Flight SK-404!\n"
                f"Details:\n"
                f"- Seat: 14A (Window)\n"
                f"- Cabin: Economy\n"
                f"- Checked Luggage: 2 bags transferred automatically\n\n"
                f"Additionally, I have issued your complimentary $30 meal voucher:\n"
                f"- Voucher Code: {json.loads(voucher)['voucher_code']}\n\n"
                f"Is there anything else I can assist you with today?"
            )
        return (
            "[MOCK AGENT NOTICE: Set your GEMINI_API_KEY in .env to enable the full autonomous Gemini agent]\n\n"
            "Hello! Welcome to SkyCare Airline Support. Could you please provide your 6-character PNR code and last name?"
        )

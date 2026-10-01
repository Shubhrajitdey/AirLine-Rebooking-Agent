# ✈️ SkyCare: Airline Rebooking AI Agent

An autonomous, empathetic, and policy-compliant AI agent powered by **Google Gemini API** (using the new `google-genai` SDK) designed to assist passengers during flight disruptions (cancellations, long delays, missed connections).

---

## 📁 Project Structure

```text
Airline Rebooking Agent/
├── .env.example              # Environment variables template (Gemini API Key)
├── .gitignore                # Git ignore configuration
├── Problem.md                # Detailed problem statement and requirements
├── README.md                 # Documentation and setup instructions
├── requirements.txt          # Python dependencies
├── main.py                   # Interactive CLI chat runner
├── data/
│   └── sample_data.json      # Mock airline inventory, bookings & passenger PNRs
├── src/
│   ├── __init__.py
│   ├── config.py             # Environment & configuration loader
│   ├── models.py             # Pydantic data schemas
│   ├── prompts.py            # Agent persona, policy & system instructions
│   ├── tools.py              # Tool/Function calling interfaces
│   └── agent.py              # Gemini client initialization & chat loop
└── tests/
    └── test_agent.py         # Unit tests for tools and policy logic
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (or Python 3.9+)
- A Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### 2. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure API Key
Copy the example `.env` file and insert your Gemini API Key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

> **Note**: If `GEMINI_API_KEY` is not set, the agent operates in an interactive **Demo / Mock Mode** so you can preview the CLI and workflow immediately.

### 4. Run the Agent CLI
```bash
python3 main.py
```

### 5. Run Tests
```bash
pytest tests/
```

---

## 🛠️ Integrated Gemini Function Tools
The agent uses Gemini tool/function calling with the following interfaces:
1. `get_booking_details(pnr, last_name)`: Verifies passenger identity and retrieves current flight disruption details.
2. `search_flights(origin, destination, travel_date)`: Searches available flights with real-time seat availability.
3. `check_rebooking_policy(pnr)`: Validates free rebooking eligibility, waiver rules, and loyalty perks.
4. `rebook_flight(pnr, new_flight_number, seat_preference)`: Executes the transactional rebooking and transfers luggage.
5. `issue_voucher(pnr, voucher_type)`: Issues complimentary meal or hotel vouchers for eligible disruptions.

---

## 🧪 Sample Test Data
Use these sample records in the CLI to test different disruption scenarios:
- **PNR: `SKY101`** (Passenger: *John Doe*)
  - Route: SFO ➔ JFK
  - Status: **CANCELLED** (Severe Weather)
  - Tier: **Platinum** (Eligible for free rebooking, upgrades, and meal vouchers)
- **PNR: `SKY202`** (Passenger: *Sarah Connor*)
  - Route: ORD ➔ LAX
  - Status: **DELAYED** (4-hour mechanical delay)
  - Tier: **Silver**
- **PNR: `SKY303`** (Passenger: *David Smith*)
  - Route: SEA ➔ MIA
  - Status: **ON TIME**
  - Tier: **Regular**

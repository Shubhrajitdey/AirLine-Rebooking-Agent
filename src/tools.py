import json
import uuid
from typing import Dict, Any, Optional
from src.config import SAMPLE_DATA_FILE

def _load_data() -> Dict[str, Any]:
    with open(SAMPLE_DATA_FILE, "r") as f:
        return json.load(f)

def _save_data(data: Dict[str, Any]) -> None:
    with open(SAMPLE_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_booking_details(pnr: str, last_name: str) -> str:
    """Lookup booking and disruption status for a passenger given their PNR and last name.
    
    Args:
        pnr: The 6-character Passenger Name Record code (e.g. 'SKY101').
        last_name: The passenger's last name for verification.
    """
    data = _load_data()
    pnr_clean = pnr.strip().upper()
    booking = data.get("bookings", {}).get(pnr_clean)
    
    if not booking:
        return json.dumps({"error": f"No booking found for PNR '{pnr_clean}'."})
    
    if booking["passenger"]["last_name"].lower() != last_name.strip().lower():
        return json.dumps({"error": f"Last name does not match the record for PNR '{pnr_clean}'."})
    
    return json.dumps(booking, indent=2)

def search_flights(origin: str, destination: str, travel_date: Optional[str] = None) -> str:
    """Search available flights between origin and destination airport codes.
    
    Args:
        origin: 3-letter IATA airport code (e.g. 'SFO', 'ORD').
        destination: 3-letter IATA airport code (e.g. 'JFK', 'LAX').
        travel_date: Optional date string in YYYY-MM-DD format.
    """
    data = _load_data()
    flights = data.get("flights", [])
    
    matches = [
        f for f in flights
        if f["origin"].upper() == origin.strip().upper()
        and f["destination"].upper() == destination.strip().upper()
    ]
    
    if travel_date:
        matches = [f for f in matches if f["departure_time"].startswith(travel_date.strip())]
        
    if not matches:
        return json.dumps({
            "message": f"No flights found from {origin.upper()} to {destination.upper()}" + (f" on {travel_date}" if travel_date else "")
        })
        
    return json.dumps(matches, indent=2)

def check_rebooking_policy(pnr: str) -> str:
    """Evaluate rebooking eligibility, waivers, and loyalty benefits for a given booking.
    
    Args:
        pnr: The 6-character PNR code.
    """
    data = _load_data()
    booking = data.get("bookings", {}).get(pnr.strip().upper())
    
    if not booking:
        return json.dumps({"error": f"Booking not found for PNR '{pnr}'."})
        
    status = booking.get("status", "")
    delay = booking.get("delay_minutes", 0)
    loyalty = booking.get("passenger", {}).get("loyalty_tier", "Regular")
    
    eligible_free = (status == "CANCELLED") or (status == "DELAYED" and delay >= 120)
    upgrade_eligible = loyalty in ["Platinum", "Gold"]
    meal_voucher = delay >= 180 or status == "CANCELLED"
    hotel_voucher = status == "CANCELLED" or delay >= 360
    
    policy_summary = {
        "pnr": pnr.strip().upper(),
        "status": status,
        "eligible_for_free_rebooking": eligible_free,
        "waiver_fee_applicable": False if eligible_free else True,
        "free_rebooking_window_days": 3 if eligible_free else 0,
        "upgrade_eligible": upgrade_eligible,
        "eligible_for_meal_voucher": meal_voucher,
        "eligible_for_hotel_voucher": hotel_voucher,
        "loyalty_tier": loyalty,
        "policy_explanation": (
            "Flight is severely disrupted or cancelled. Customer is entitled to free rebooking "
            "within a 3-day window at zero fare difference." if eligible_free else
            "Flight is operating normally or disruption is minor. Standard change fees apply."
        )
    }
    
    return json.dumps(policy_summary, indent=2)

def rebook_flight(pnr: str, new_flight_number: str, seat_preference: Optional[str] = "Window") -> str:
    """Execute the rebooking transaction, assign seat, and update the passenger's itinerary.
    
    Args:
        pnr: The 6-character PNR code.
        new_flight_number: The flight number selected for rebooking (e.g. 'SK-404').
        seat_preference: Preferred seat type ('Window', 'Aisle', 'Middle').
    """
    data = _load_data()
    pnr_clean = pnr.strip().upper()
    booking = data.get("bookings", {}).get(pnr_clean)
    
    if not booking:
        return json.dumps({"error": f"No booking found for PNR '{pnr_clean}'."})
        
    flights = data.get("flights", [])
    target_flight = next((f for f in flights if f["flight_number"].upper() == new_flight_number.strip().upper()), None)
    
    if not target_flight:
        return json.dumps({"error": f"Flight '{new_flight_number}' not found in schedule inventory."})
        
    cabin = booking.get("cabin_class", "Economy")
    if target_flight["available_seats"].get(cabin, 0) <= 0:
        # Check upgrade eligibility if loyalty tier permits
        loyalty = booking.get("passenger", {}).get("loyalty_tier", "Regular")
        if loyalty in ["Platinum", "Gold"] and target_flight["available_seats"].get("Business", 0) > 0:
            cabin = "Business"
        else:
            return json.dumps({"error": f"No seats available in {cabin} class on flight '{new_flight_number}'."})
            
    # Decrement seat inventory
    target_flight["available_seats"][cabin] -= 1
    
    old_flight = booking["flight_number"]
    booking["flight_number"] = target_flight["flight_number"]
    booking["scheduled_departure"] = target_flight["departure_time"]
    booking["scheduled_arrival"] = target_flight["arrival_time"]
    booking["status"] = "CONFIRMED"
    booking["delay_minutes"] = 0
    booking["disruption_reason"] = None
    booking["cabin_class"] = cabin
    
    assigned_seat = f"14A ({seat_preference})" if seat_preference else "14A"
    booking["seat"] = assigned_seat
    
    confirmation_code = f"RBK-{uuid.uuid4().hex[:8].upper()}"
    
    _save_data(data)
    
    confirmation = {
        "status": "SUCCESS",
        "confirmation_code": confirmation_code,
        "pnr": pnr_clean,
        "passenger": f"{booking['passenger']['first_name']} {booking['passenger']['last_name']}",
        "old_flight": old_flight,
        "new_flight": target_flight["flight_number"],
        "route": f"{target_flight['origin']} -> {target_flight['destination']}",
        "departure_time": target_flight["departure_time"],
        "arrival_time": target_flight["arrival_time"],
        "seat": assigned_seat,
        "cabin_class": cabin,
        "checked_bags_transferred": booking.get("checked_bags", 0),
        "message": f"Successfully rebooked onto flight {target_flight['flight_number']}."
    }
    
    return json.dumps(confirmation, indent=2)

def issue_voucher(pnr: str, voucher_type: str) -> str:
    """Issue a digital meal or hotel amenity voucher for disrupted passengers.
    
    Args:
        pnr: The 6-character PNR code.
        voucher_type: Type of voucher ('MEAL', 'HOTEL', 'TRANSPORT').
    """
    data = _load_data()
    booking = data.get("bookings", {}).get(pnr.strip().upper())
    
    if not booking:
        return json.dumps({"error": f"Booking '{pnr}' not found."})
        
    code = f"VCHR-{voucher_type.upper()}-{uuid.uuid4().hex[:6].upper()}"
    amount = "$30 Food & Beverage" if voucher_type.upper() == "MEAL" else "$150 Hotel Accommodation"
    
    voucher = {
        "voucher_code": code,
        "pnr": pnr.strip().upper(),
        "voucher_type": voucher_type.upper(),
        "value": amount,
        "valid_until": "48 Hours from issuance",
        "instructions": "Present this digital barcode at participating airport concessionaires or hotel desks."
    }
    
    return json.dumps(voucher, indent=2)

# Tool registry list for Gemini API
TOOLS = [
    get_booking_details,
    search_flights,
    check_rebooking_policy,
    rebook_flight,
    issue_voucher
]

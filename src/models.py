from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class Passenger(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    loyalty_tier: str = Field(description="Regular, Silver, Gold, Platinum")

class Booking(BaseModel):
    pnr: str
    passenger: Passenger
    flight_number: str
    origin: str
    destination: str
    scheduled_departure: str
    scheduled_arrival: str
    status: str = Field(description="CONFIRMED, DELAYED, CANCELLED, ON_TIME")
    delay_minutes: int = 0
    disruption_reason: Optional[str] = None
    cabin_class: str
    seat: str
    checked_bags: int = 0

class FlightOption(BaseModel):
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    available_seats: Dict[str, int]
    aircraft: str
    is_direct: bool = True

class PolicyCheckResult(BaseModel):
    pnr: str
    eligible_for_free_rebooking: bool
    free_rebooking_window_days: int
    upgrade_eligible: bool
    eligible_for_meal_voucher: bool
    eligible_for_hotel_voucher: bool
    policy_notes: str

class RebookingConfirmation(BaseModel):
    pnr: str
    passenger_name: str
    old_flight: str
    new_flight: str
    origin: str
    destination: str
    departure_time: str
    seat: str
    cabin_class: str
    luggage_transferred: bool
    confirmation_code: str
    status: str = "CONFIRMED"

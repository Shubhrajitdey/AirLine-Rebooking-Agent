import json
import pytest
from src.tools import (
    get_booking_details,
    search_flights,
    check_rebooking_policy,
    rebook_flight,
    issue_voucher
)

def test_get_booking_details_valid():
    res = json.loads(get_booking_details("SKY101", "Doe"))
    assert "pnr" in res
    assert res["pnr"] == "SKY101"
    assert res["status"] == "CANCELLED"
    assert res["passenger"]["loyalty_tier"] == "Platinum"

def test_get_booking_details_invalid_name():
    res = json.loads(get_booking_details("SKY101", "WrongName"))
    assert "error" in res

def test_search_flights():
    res = json.loads(search_flights("SFO", "JFK"))
    assert isinstance(res, list)
    assert len(res) >= 2
    assert all(f["origin"] == "SFO" and f["destination"] == "JFK" for f in res)

def test_check_rebooking_policy_cancelled():
    res = json.loads(check_rebooking_policy("SKY101"))
    assert res["eligible_for_free_rebooking"] is True
    assert res["upgrade_eligible"] is True
    assert res["eligible_for_meal_voucher"] is True

def test_check_rebooking_policy_on_time():
    res = json.loads(check_rebooking_policy("SKY303"))
    assert res["eligible_for_free_rebooking"] is False

def test_rebooking_flow():
    res = json.loads(rebook_flight("SKY101", "SK-404", "Aisle"))
    assert res["status"] == "SUCCESS"
    assert res["new_flight"] == "SK-404"
    assert "Aisle" in res["seat"]

def test_issue_voucher():
    res = json.loads(issue_voucher("SKY101", "MEAL"))
    assert "voucher_code" in res
    assert res["voucher_type"] == "MEAL"

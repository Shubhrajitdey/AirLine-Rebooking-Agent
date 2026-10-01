from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional

class DisruptionCode(str, Enum):
    WEATHER = "WEATHER"
    MECHANICAL = "MECHANICAL"
    CREW_TIMEOUT = "CREW_TIMEOUT"
    AIR_TRAFFIC = "AIR_TRAFFIC"
    UNSPECIFIED = "UNSPECIFIED"

class PassengerIntent(str, Enum):
    REBOOK = "REBOOK"
    REFUND = "REFUND"
    INQUIRY = "INQUIRY"
    UNKNOWN = "UNKNOWN"

class EventStatus(str, Enum):
    INITIATED = "INITIATED"
    SUCCESS = "SUCCESS"
    RETRIED = "RETRIED"
    FAILED = "FAILED"

@dataclass
class ExecutionEvent:
    event_name: str
    stage: str
    status: EventStatus
    retry_count: int = 0

@dataclass
class PolicyTrace:
    policy_name: str
    rule_evaluated: str
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RebookingResponse:
    decision: str
    customer_response: str
    waiver_applied: bool
    requires_confirmation: bool
    offered_flight: Optional[str] = None
    events: List[ExecutionEvent] = field(default_factory=list)

@dataclass
class ExtractedContext:
    raw_query: str
    intent: PassengerIntent
    pnr: Optional[str]
    disruption_code: DisruptionCode
    requested_date: Optional[str]
    confidence_score: float = 1.0
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)

@dataclass
class AgentRegistry:
    InterpretorAgent : Any
    BookingAgent : Any

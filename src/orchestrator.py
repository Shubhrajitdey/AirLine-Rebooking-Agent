import re
import json
import datetime
from typing import Dict, Any, List, Tuple, Optional

from src.models import (
    ExtractedContext, PassengerIntent, DisruptionCode,
    ExecutionEvent, PolicyTrace, EventStatus, AgentRegistry
)

class Orchestrator:
    def __init__(self, registry: Optional[AgentRegistry] = None, inventory: Optional[Dict[str, Any]] = None):
        self.registry = registry
        self.CONFIDENCE_THRESHOLD = 0.38  # 38% rule
        self.inventory = inventory or {
            "SK-101": {"departure": "2026-10-02 08:30", "seats": 2},
            "SK-202": {"departure": "2026-10-02 14:00", "seats": 0}
        }
        self.metrics = {
            "total_requests": 0,
            "successful": 0,
            "validation_failures": 0,
            "policy_rejections": 0,
            "escalations": 0
        }

    def parse_json_safely(self, text: str) -> Dict[str, Any]:
        """Strips markdown fences and extracts valid JSON objects."""
        clean = text.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```(?:json)?\s*", "", clean)
            clean = re.sub(r"\s*```$", "", clean)
        clean = clean.strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            match = re.search(r"(\{.*\})", clean, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            raise ValueError(f"Cannot parse JSON from: {text[:100]}")

    def is_valid_input(self, text: str) -> bool:
        return bool(text and isinstance(text, str) and len(text.strip()) >= 6 and any(c.isalnum() for c in text))

    def is_valid_pnr(self, pnr: Optional[str]) -> bool:
        return bool(pnr and len(pnr) == 6 and pnr.isalnum() and pnr.isupper())

    def is_valid_date(self, date_str: Optional[str]) -> bool:
        if not date_str:
            return True
        try:
            target = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            return target >= datetime.date.today()
        except ValueError:
            return False

    def validate_context(self, ctx: ExtractedContext) -> Tuple[bool, List[str]]:
        errors = []
        if ctx.intent == PassengerIntent.UNKNOWN:
            errors.append("UNKNOWN_INTENT")
        if not self.is_valid_pnr(ctx.pnr):
            errors.append("INVALID_OR_MISSING_PNR")
        if ctx.requested_date and not self.is_valid_date(ctx.requested_date):
            errors.append("INVALID_OR_EXPIRED_DATE")
        return len(errors) == 0, errors

    def check_inventory(self, events: List[ExecutionEvent]) -> Tuple[Optional[str], Optional[str]]:
        for fl_no, info in self.inventory.items():
            if info["seats"] > 0:
                events.append(ExecutionEvent(
                    event_name="INVENTORY_MATCH",
                    stage="INVENTORY",
                    status=EventStatus.SUCCESS
                ))
                return fl_no, info["departure"]
        return None, None

    def invoke_booking_with_retry(self, agent: Any, payload: Dict[str, Any], 
                                 events: List[ExecutionEvent], max_retries: int = 2) -> Dict[str, Any]:
        retries = 0
        while retries <= max_retries:
            events.append(ExecutionEvent(
                event_name="BOOKING_LLM_CALL",
                stage="AGENT_INVOCATION",
                status=EventStatus.INITIATED if retries == 0 else EventStatus.RETRIED,
                retry_count=retries
            ))
            try:
                raw_text = agent.invoke(payload)
                result = self.parse_json_safely(raw_text)
                events.append(ExecutionEvent(
                    event_name="BOOKING_LLM_CALL",
                    stage="AGENT_INVOCATION",
                    status=EventStatus.SUCCESS,
                    retry_count=retries
                ))
                return result
            except Exception as e:
                events.append(ExecutionEvent(
                    event_name="BOOKING_LLM_CALL_FAILED",
                    stage="AGENT_INVOCATION",
                    status=EventStatus.FAILED,
                    retry_count=retries
                ))
                retries += 1

        return {
            "decision": "ESCALATE_TO_HUMAN",
            "customer_response": "We experienced a temporary system error. A gate agent will assist you.",
            "waiver_applied": False,
            "offered_flight": None,
            "requires_confirmation": False
        }

    def decision(self, user_query: str) -> str:
        self.metrics["total_requests"] += 1
        events: List[ExecutionEvent] = []
        traces: List[PolicyTrace] = []

        # 1. Gate: Input sanity
        if not self.is_valid_input(user_query):
            self.metrics["validation_failures"] += 1
            traces.append(PolicyTrace("INPUT_SANITY", "min_length_6_alnum", False))
            return self._build_json("FAILED", None, traces, events, "Malformed or empty query.")
        traces.append(PolicyTrace("INPUT_SANITY", "min_length_6_alnum", True))

        # 2. Invoke Interpreter
        interpreter = self.registry.InterpretorAgent if self.registry else AgentRegistry.get("agent:interpreter")
        raw_interp = interpreter.invoke(user_query)

        try:
            parsed = self.parse_json_safely(raw_interp)
            ctx = ExtractedContext(
                raw_query=user_query,
                intent=PassengerIntent(parsed.get("intent", "UNKNOWN")),
                pnr=parsed.get("pnr"),
                disruption_code=DisruptionCode(parsed.get("disruption_code", "UNSPECIFIED")),
                requested_date=parsed.get("requested_date"),
                confidence_score=float(parsed.get("confidence_score", 0.0))
            )
        except Exception:
            ctx = ExtractedContext(
                raw_query=user_query,
                intent=PassengerIntent.UNKNOWN,
                pnr=None,
                disruption_code=DisruptionCode.UNSPECIFIED,
                requested_date=None,
                confidence_score=0.10
            )

        # 3. Gate: 38% Confidence Guardrail
        conf_passed = ctx.confidence_score >= self.CONFIDENCE_THRESHOLD
        traces.append(PolicyTrace("CONFIDENCE_GUARDRAIL_38_PCT", f">= {self.CONFIDENCE_THRESHOLD}", conf_passed, {"score": ctx.confidence_score}))

        if not conf_passed:
            self.metrics["escalations"] += 1
            events.append(ExecutionEvent("HALLUCINATION_GUARD", "GUARDRAIL", EventStatus.FAILED))
            payload = {
                "decision": "ESCALATE_TO_HUMAN",
                "customer_response": "Connecting you with customer care to verify itinerary details.",
                "waiver_applied": False,
                "offered_flight": None,
                "requires_confirmation": False
            }
            return self._build_json("ESCALATED", ctx, traces, events, payload)

        # 4. Gate: Slot Validation
        is_valid, errs = self.validate_context(ctx)
        ctx.is_valid = is_valid
        ctx.validation_errors = errs
        traces.append(PolicyTrace("SLOT_VALIDATION", "valid_pnr_and_date", is_valid, {"errors": errs}))

        if not is_valid:
            self.metrics["validation_failures"] += 1
            return self._build_json("FAILED", ctx, traces, events, {"errors": errs})

        # 5. Gate: Disruption Waiver Policy
        waiver_eligible = ctx.disruption_code in [DisruptionCode.WEATHER, DisruptionCode.MECHANICAL, DisruptionCode.CREW_TIMEOUT]
        traces.append(PolicyTrace("DISRUPTION_WAIVER_RULE", "eligible_disruption_code", waiver_eligible))

        # 6. Check Inventory
        matched_flight, departure_time = self.check_inventory(events)
        traces.append(PolicyTrace("INVENTORY_RULE", "seats_available", matched_flight is not None))

        # 7. Booking Agent Call
        booking_agent = self.registry.BookingAgent if self.registry else AgentRegistry.get("agent:booking")
        booking_payload = self.invoke_booking_with_retry(
            booking_agent,
            {
                "pnr": ctx.pnr,
                "disruption_code": ctx.disruption_code.value,
                "waiver_applicable": waiver_eligible,
                "available_flight": matched_flight,
                "departure_time": departure_time
            },
            events
        )

        # 8. Set Final Status & Increment Cumulative Metrics
        if booking_payload.get("decision") == "ESCALATE_TO_HUMAN":
            self.metrics["escalations"] += 1
            final_status = "ESCALATED"
        elif matched_flight:
            self.metrics["successful"] += 1
            final_status = "SUCCESS"
        else:
            self.metrics["policy_rejections"] += 1
            final_status = "POLICY_REJECTED"

        return self._build_json(final_status, ctx, traces, events, booking_payload)

    def _build_json(self, status: str, ctx: Optional[ExtractedContext],
                    traces: List[PolicyTrace], events: List[ExecutionEvent],
                    resolution: Any) -> str:
        data = {
            "status": status,
            "extracted_slots": {
                "pnr": ctx.pnr if ctx else None,
                "intent": ctx.intent.value if ctx else "UNKNOWN",
                "disruption_code": ctx.disruption_code.value if ctx else "UNSPECIFIED",
                "requested_date": ctx.requested_date if ctx else None,
                "confidence": ctx.confidence_score if ctx else 0.0
            },
            "resolution": resolution,
            "telemetry": {
                "total_events": len(events),
                "events": [
                    {
                        "event_name": e.event_name,
                        "stage": e.stage,
                        "status": e.status.value,
                        "retry_count": e.retry_count,
                        "metadata": getattr(e, "metadata", {})
                    }
                    for e in events
                ],
                "total_traces": len(traces),
                "traces": [
                    {
                        "policy": t.policy_name,
                        "rule": t.rule_evaluated,
                        "passed": t.passed,
                        "details": t.details
                    }
                    for t in traces
                ],
                "metrics": {
                    "total_requests": self.metrics["total_requests"],
                    "successful": self.metrics["successful"],
                    "validation_failures": self.metrics["validation_failures"],
                    "policy_rejections": self.metrics["policy_rejections"],
                    "escalations": self.metrics["escalations"],
                    "success_rate": (
                        round(self.metrics["successful"] / self.metrics["total_requests"], 2)
                        if self.metrics["total_requests"] > 0 else 0.0
                    )
                }
            }
        }
        return json.dumps(data, indent=2)
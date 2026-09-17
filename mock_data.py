"""De-identified, deterministic access-network repair simulations.

Every datum is synthetic and exists solely for safe WSO2 Agent Manager demonstrations.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SCENARIOS: dict[str, dict[str, Any]] = {
    "repeated-ftth-optical-power-fault": {
        "id": "FIELD-SIM-2026-0917-001",
        "title": "Repeated FTTH optical-power failure at a shared distribution cabinet",
        "assessment_time": "2026-09-17T06:30:00Z",
        "trigger": "Dispatch assignment for a third repeat trouble ticket within fourteen days.",
        "fault_domain": "FTTH outside plant / passive optical distribution",
        "work_order": {
            "id": "SIM-WO-2026-0917-188",
            "priority": "P2",
            "status": "Assigned — technician briefing required",
            "customer_impact": "One residential subscriber is down; two nearby subscriber records show intermittent low optical margin.",
            "ticket_link": "mock://tickets/SIM-TT-2026-0917-188",
        },
        "site": {
            "asset": "SIM-FDP-BKK-042",
            "site_type": "Fiber distribution cabinet",
            "service_area": "Bang Kapi serving area, synthetic zone 4",
            "access_constraints": "Access only during the approved 07:00–17:00 local work window. Verify the cabinet identifier before opening.",
            "environment": "Outdoor cabinet; wet-weather conditions were recorded during the previous visit.",
        },
        "alarm_and_measurement_evidence": {
            "alarm_summary": "OLT reports loss of signal for SIM-ONT-77841. The feeder PON remains up; two adjacent drops show reduced downstream optical margin.",
            "latest_measurements": "Last remote reading: ONT receive power −29.1 dBm. Adjacent reference lines: −24.7 dBm and −25.2 dBm. These values are synthetic and require on-site verification.",
            "correlation": "The affected ONT and the two low-margin adjacent drops share splitter leg S04 on SIM-FDP-BKK-042.",
            "confidence": "Medium: shared-leg pattern is consistent with a local passive-path issue, but no physical cause is confirmed.",
        },
        "history": [
            "SIM-WO-2026-0905-077: connector cleaning and visual inspection recorded; optical level temporarily improved.",
            "SIM-WO-2026-0911-133: no feeder alarm found; technician noted moisture near the lower cable-entry gland.",
            "No approved civil work or planned maintenance overlaps the current report.",
        ],
        "safety_notes": [
            "Follow the operator's current field-safety procedure and local site-risk assessment before beginning work.",
            "Do not look into fiber ends, connectors, splitters, or test ports. Use approved fiber-safety controls and equipment only.",
            "Do not bypass cabinet security, electrical isolation requirements, weather restrictions, or traffic-control procedures.",
            "Stop work and contact the designated supervisor if the asset identifier, access condition, or safety condition differs from the work order.",
        ],
        "recommended_tests": [
            "Confirm the cabinet, splitter leg, subscriber identifier, and scope against the assigned work order before handling any asset.",
            "Review the visible condition of the cabinet, seals, cable entries, and approved grounding and safety controls; record observations rather than inferring a cause.",
            "Use the approved optical test procedure to compare the affected drop with the two synthetic reference drops on splitter leg S04.",
            "If the approved procedure identifies a loss boundary, capture the approved measurement output and photograph the relevant labelled asset condition before any authorized remediation.",
            "Escalate to the fiber-maintenance owner if evidence indicates a shared passive-path issue or if the approved test result contradicts the remote evidence.",
        ],
        "suggested_spares": [
            "Approved SC/APC field connector kit",
            "Approved weatherproof cable-entry seal/gland kit",
            "Labelled dust caps and cleaning consumables approved by the operator",
        ],
        "closure_evidence": [
            "Verified cabinet and splitter-leg identifiers",
            "Before-and-after optical measurements recorded using the approved method",
            "Photographs of labelled asset condition and any replaced approved part",
            "Technician observations, safety exceptions, and escalation reference if no restore is confirmed",
            "Supervisor-approved service-restored declaration before ticket closure",
        ],
        "approval_gates": [
            "Dispatcher or supervisor approval before reassignment or a change in job priority.",
            "Inventory-system approval before reserving or consuming a spare outside the assigned kit.",
            "Authorized technician and supervisor confirmation before declaring service restored or closing a ticket.",
            "Network owner approval before any network configuration, splitter redesign, or capacity action.",
        ],
    },
    "fixed-wireless-intermittent-cpe-link": {
        "id": "FIELD-SIM-2026-0917-002",
        "title": "Intermittent fixed-wireless CPE link following severe weather",
        "assessment_time": "2026-09-17T08:10:00Z",
        "trigger": "Repeat dispatch after intermittent customer-premises equipment link degradation.",
        "fault_domain": "Fixed wireless access / customer-premises equipment",
        "work_order": {
            "id": "SIM-WO-2026-0917-206",
            "priority": "P3",
            "status": "Assigned — weather and access review required",
            "customer_impact": "A single small-business broadband service has intermittent throughput and link-flap reports.",
            "ticket_link": "mock://tickets/SIM-TT-2026-0917-206",
        },
        "site": {
            "asset": "SIM-FWA-CPE-119",
            "site_type": "Customer-premises wireless receiver",
            "service_area": "Synthetic industrial estate 7",
            "access_constraints": "Customer appointment is recorded; roof access is not authorized in high wind or lightning conditions.",
            "environment": "Previous weather event included heavy rain and wind; current site condition is unverified.",
        },
        "alarm_and_measurement_evidence": {
            "alarm_summary": "Radio link has six brief down/up events in the preceding twelve hours; serving sector remains available.",
            "latest_measurements": "Remote signal trend changed from −61 dBm to −72 dBm. Modulation shifted down twice. Values require on-site confirmation.",
            "correlation": "No broad sector outage pattern is visible in the synthetic evidence.",
            "confidence": "Medium: evidence suggests a local alignment, mount, cable, or environmental condition but does not identify one.",
        },
        "history": [
            "SIM-WO-2026-0829-044: mounting hardware retightened after vibration report.",
            "No record of a CPE replacement in the last twelve months.",
            "Last customer contact reported intermittent service after the weather event.",
        ],
        "safety_notes": [
            "Perform the site-risk assessment before any roof, mast, ladder, or electrical work.",
            "Do not work at height during unsafe weather or without the required authorization and fall-protection controls.",
            "Do not alter radio parameters, transmit power, or spectrum settings; these are not field-copilot actions.",
            "Stop and escalate when access, structural condition, or electrical safety is uncertain.",
        ],
        "recommended_tests": [
            "Verify the customer appointment, equipment identifier, and current weather/access conditions before starting work.",
            "Use the approved visual and mechanical inspection procedure to assess labelled mounting, cable routing, weatherproofing, and grounding condition.",
            "Capture approved local link statistics and compare them with the synthetic remote trend; do not treat the trend as a confirmed root cause.",
            "If the approved procedure permits, perform the prescribed alignment and connectivity validation, then document before-and-after observations.",
            "Escalate suspected structural, lightning-protection, or sector-level issues through the assigned workflow.",
        ],
        "suggested_spares": [
            "Approved outdoor-rated patch lead",
            "Approved weatherproofing kit",
            "Approved mounting-hardware kit only when authorized by the work order",
        ],
        "closure_evidence": [
            "Current weather and access assessment",
            "Photographs of labelled CPE, mount, cable, and weatherproofing condition",
            "Approved before-and-after link statistics",
            "Customer-side service validation result or an escalation reference",
            "Supervisor-approved closure decision",
        ],
        "approval_gates": [
            "Supervisor approval for any work-at-height exception, reassignment, or additional visit.",
            "Inventory approval before spare consumption beyond the assigned kit.",
            "Network-engineering approval for any radio configuration action.",
            "Authorized technician and supervisor confirmation before service-restored declaration or ticket closure.",
        ],
    },
    "small-cell-power-and-backhaul-alarm": {
        "id": "FIELD-SIM-2026-0917-003",
        "title": "Small-cell power and backhaul alarm with uncertain local-site condition",
        "assessment_time": "2026-09-17T10:05:00Z",
        "trigger": "Access-network dispatch for a small cell reporting power and backhaul alarms.",
        "fault_domain": "Mobile access / small-cell site infrastructure",
        "work_order": {
            "id": "SIM-WO-2026-0917-224",
            "priority": "P2",
            "status": "Assigned — facilities coordination required",
            "customer_impact": "Synthetic local coverage reduction; no emergency-service impact is represented in this simulation.",
            "ticket_link": "mock://tickets/SIM-TT-2026-0917-224",
        },
        "site": {
            "asset": "SIM-SC-BKK-311",
            "site_type": "Street-level small-cell enclosure",
            "service_area": "Synthetic central business district 2",
            "access_constraints": "Facilities escort and municipal access permit must be confirmed before enclosure work.",
            "environment": "Public right-of-way; temporary traffic and pedestrian controls may be required by the approved work plan.",
        },
        "alarm_and_measurement_evidence": {
            "alarm_summary": "Power supply alarm preceded an ethernet backhaul loss by four minutes. Adjacent cells remain normal in the synthetic feed.",
            "latest_measurements": "Remote telemetry last reported a low DC input warning before the unit became unreachable.",
            "correlation": "The alarm ordering is compatible with several site-local explanations; it is not proof of a power fault.",
            "confidence": "Low to medium: remote telemetry is incomplete after loss of reachability.",
        },
        "history": [
            "SIM-WO-2026-0718-022: enclosure gasket replaced after water-ingress concern.",
            "SIM-WO-2026-0901-091: facilities vendor reported a nearby civil work activity; no confirmed impact recorded.",
            "No approved maintenance is associated with the current alarm window.",
        ],
        "safety_notes": [
            "Obtain the required facilities escort, access permit, and site-risk assessment before opening any enclosure.",
            "Do not perform electrical isolation, energization, or work on live equipment unless you hold the required authorization and follow the approved procedure.",
            "Use the approved pedestrian and traffic controls for public-right-of-way work.",
            "Treat water ingress, damaged cabling, or exposed electrical hazards as stop-work and escalation conditions.",
        ],
        "recommended_tests": [
            "Confirm permit, escort, asset label, and public-area control requirements before site access.",
            "Use the approved non-invasive inspection procedure to record enclosure condition, external power indications, cable condition, and evidence of environmental ingress.",
            "Perform only the authorized power and backhaul verification tests; retain the raw approved readings with timestamp and asset label.",
            "Compare local findings with the remote alarm ordering without declaring a root cause from either source alone.",
            "Escalate electrical, facilities, civil-work, or backhaul findings to the corresponding authorized owner.",
        ],
        "suggested_spares": [
            "Approved enclosure gasket kit",
            "Approved outdoor ethernet patch lead",
            "Approved labelled fuse or power module only when explicitly authorized",
        ],
        "closure_evidence": [
            "Permit, escort, and public-area control confirmation",
            "Labelled site photographs and approved inspection findings",
            "Authorized power and backhaul test results",
            "Any owner escalation reference and outstanding safety condition",
            "Authorized service-restored confirmation before closure",
        ],
        "approval_gates": [
            "Facilities and access approval before enclosure work.",
            "Electrical-authority approval for isolation, energization, fuse, or power-module work.",
            "Inventory approval before replacing a controlled spare.",
            "Authorized technician and supervisor confirmation before declaring restoration or closing the ticket.",
        ],
    },
}


def scenarios() -> list[dict[str, str]]:
    """Return compact, non-sensitive simulation metadata."""
    return [
        {
            "scenario_id": scenario_id,
            "work_order_id": item["work_order"]["id"],
            "title": item["title"],
            "fault_domain": item["fault_domain"],
        }
        for scenario_id, item in SCENARIOS.items()
    ]


def scenario_data(scenario_id: str) -> dict[str, Any]:
    """Return an isolated scenario copy so evidence cannot be mutated."""
    return deepcopy(SCENARIOS[scenario_id])

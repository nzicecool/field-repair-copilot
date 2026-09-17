"""Read-only evidence selection and deterministic access-network repair briefs."""

from __future__ import annotations

from typing import Any

from mock_data import SCENARIOS, scenario_data, scenarios


class ScenarioNotFound(ValueError):
    """Raised when a caller explicitly requests an unavailable simulation."""


def select_scenario(message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Select one synthetic scenario without accessing any external system."""
    context = context or {}
    requested = str(context.get("scenario_id", "")).strip().lower()
    if requested:
        if requested not in SCENARIOS:
            raise ScenarioNotFound(f"No mock field-repair scenario matches `{requested}`.")
        return scenario_data(requested)

    text = message.lower().replace("_", "-")
    # Test the specific fiber vocabulary before generic shared terms such as
    # "power".  Otherwise an FTTH optical-power query could select the small-
    # cell power-and-backhaul simulation instead of the intended fiber brief.
    if any(
        term in text
        for term in (
            "ftth",
            "fiber",
            "fibre",
            "optical",
            "pon",
            "olt",
            "ont",
            "splitter",
            "fdf",
            "fdp",
        )
    ):
        return scenario_data("repeated-ftth-optical-power-fault")
    if any(term in text for term in ("wireless", "cpe", "roof", "weather", "link flap")):
        return scenario_data("fixed-wireless-intermittent-cpe-link")
    if any(term in text for term in ("small cell", "power", "backhaul", "enclosure", "cell")):
        return scenario_data("small-cell-power-and-backhaul-alarm")
    return scenario_data("repeated-ftth-optical-power-fault")


def list_scenarios_report() -> str:
    """List available mock scenarios with no model invocation."""
    lines = ["# Field Repair Copilot — available simulations", ""]
    for item in scenarios():
        lines.append(
            f"- **{item['scenario_id']}** — {item['title']} "
            f"(`{item['work_order_id']}`, {item['fault_domain']})"
        )
    lines.extend(
        [
            "",
            "Use `context.scenario_id` to select a simulation. All evidence is synthetic and de-identified.",
            "",
            "## Safety boundary",
            "This is a read-only simulation. No dispatch, inventory action, physical work, network change, service-restored declaration, or ticket closure has been performed.",
        ]
    )
    return "\n".join(lines)


def build_repair_brief(scenario: dict[str, Any]) -> str:
    """Produce a complete safe fallback when a model cannot be used."""
    work_order = scenario["work_order"]
    site = scenario["site"]
    evidence = scenario["alarm_and_measurement_evidence"]
    lines = [
        "# FIELD REPAIR COPILOT — READ-ONLY REPAIR BRIEF",
        "",
        "## Assignment overview",
        f"**Simulation:** {scenario['id']} — {scenario['title']}",
        f"**Assessment time:** {scenario['assessment_time']}",
        f"**Work order:** `{work_order['id']}` ({work_order['priority']}, {work_order['status']})",
        f"**Fault domain:** {scenario['fault_domain']}",
        f"**Customer impact:** {work_order['customer_impact']}",
        "",
        "## Site and evidence",
        f"- **Asset:** `{site['asset']}` — {site['site_type']}",
        f"- **Service area:** {site['service_area']}",
        f"- **Access constraints:** {site['access_constraints']}",
        f"- **Environment:** {site['environment']}",
        f"- **Alarm summary:** {evidence['alarm_summary']}",
        f"- **Measurements:** {evidence['latest_measurements']}",
        f"- **Correlation:** {evidence['correlation']}",
        f"- **Confidence:** {evidence['confidence']}",
        "",
        "## Prior work and repeat-fault context",
    ]
    lines.extend(f"- {item}" for item in scenario["history"])
    lines.extend(["", "## Mandatory safety reminders"])
    lines.extend(f"- {item}" for item in scenario["safety_notes"])
    lines.extend(["", "## Recommended approved test sequence"])
    lines.extend(f"{index}. {item}" for index, item in enumerate(scenario["recommended_tests"], 1))
    lines.extend(["", "## Suggested approved spares"])
    lines.extend(f"- {item}" for item in scenario["suggested_spares"])
    lines.extend(["", "## Closure-evidence draft checklist"])
    lines.extend(f"- {item}" for item in scenario["closure_evidence"])
    lines.extend(["", "## Approval gates"])
    lines.extend(f"- {item}" for item in scenario["approval_gates"])
    lines.extend(
        [
            "",
            "## Safety boundary",
            "This is a read-only simulation. No dispatch, inventory action, physical work, network change, service-restored declaration, or ticket closure has been performed.",
        ]
    )
    return "\n".join(lines)

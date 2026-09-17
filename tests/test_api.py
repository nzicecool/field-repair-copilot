"""Tests for mock-data grounding, model adapters, and field-safety boundaries."""

from dataclasses import replace

from fastapi.testclient import TestClient

from main import app, copilot
from repair_llm import FieldRepairCopilot, LLMSettings, ModelUnavailable

client = TestClient(app)


class FakeCompletion:
    class Choice:
        class Message:
            content = """## Assignment and likely fault domain
- The synthetic evidence supports a passive-path investigation.

## Site-specific evidence and repeat-fault history
- The assigned asset and prior work are reviewed only from the supplied simulation.

## Mandatory safety and stop-work conditions
- Follow approved field safety controls and stop when observed conditions differ.

## Approved test sequence
- Use the approved test procedure and retain the required output.

## Suggested spares and evidence to collect
- Confirm an approved spare and collect labelled evidence before authorized remediation.

## Closure-draft requirements and approval gates
- Require the authorized technician and supervisor to approve any closure draft.
"""

        message = Message()

    choices = [Choice()]


class FakeClient:
    class Chat:
        class Completions:
            def __init__(self) -> None:
                self.calls: list[dict] = []

            def create(self, **kwargs):
                self.calls.append(kwargs)
                return FakeCompletion()

        def __init__(self) -> None:
            self.completions = self.Completions()

    def __init__(self) -> None:
        self.chat = self.Chat()


class FakeAnthropicCompletion:
    class Block:
        type = "text"
        text = """## Assignment and likely fault domain
- Review the assigned synthetic small-cell alarm only.

## Site-specific evidence and repeat-fault history
- Retain the supplied remote alarm ordering and prior work record.

## Mandatory safety and stop-work conditions
- Use only approved procedures and escalate uncertain site conditions.

## Approved test sequence
- Perform only authorized non-invasive power and backhaul verification.

## Suggested spares and evidence to collect
- Confirm approved spare authority and capture labelled observations.

## Closure-draft requirements and approval gates
- Require facilities and electrical authority approval before an authorized closure.
"""

    content = [Block()]


class FakeAnthropicClient:
    class Messages:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return FakeAnthropicCompletion()

    def __init__(self) -> None:
        self.messages = self.Messages()


def test_health_exposes_no_secrets_and_defaults_to_gemini():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["agent"] == "field-repair-copilot"
    assert payload["llm"]["provider"] == "gemini"
    assert payload["llm"]["model"] == "gemini-3-flash-preview"
    assert "api_key" not in str(payload).lower()


def test_scenarios_are_explicitly_synthetic_and_read_only():
    response = client.get("/scenarios")
    assert response.status_code == 200
    payload = response.json()
    assert payload["simulation"] is True
    assert payload["read_only"] is True
    assert {row["scenario_id"] for row in payload["scenarios"]} == {
        "repeated-ftth-optical-power-fault",
        "fixed-wireless-intermittent-cpe-link",
        "small-cell-power-and-backhaul-alarm",
    }


def test_model_response_is_grounded_keeps_history_and_has_safe_steps(monkeypatch):
    fake_client = FakeClient()
    monkeypatch.setattr(copilot, "_get_openai_client", lambda: fake_client)
    first = client.post(
        "/chat",
        json={
            "message": "Prepare an FTTH repair brief with safety and closure evidence.",
            "context": {"scenario_id": "repeated-ftth-optical-power-fault"},
            "session_id": "field-history-test",
        },
    )
    second = client.post("/chat", json={"message": "What should be captured before closure?", "session_id": "field-history-test"})
    assert first.status_code == 200
    payload = first.json()
    assert payload["provider"] == "gemini"
    assert payload["used_fallback"] is False
    assert "Safety boundary" in payload["response"]
    assert "No dispatch" in payload["response"]
    assert len(payload["development_steps"]) == 4
    assert all("reasoning" not in step.lower() for step in payload["development_steps"])
    assert second.status_code == 200
    messages = fake_client.chat.completions.calls[-1]["messages"]
    assert any(item["content"] == "Prepare an FTTH repair brief with safety and closure evidence." for item in messages)
    assert "FIELD-SIM-2026-0917-001" in messages[-1]["content"]
    assert "Do not look into fiber ends" in messages[-1]["content"]


def test_anthropic_provider_uses_native_messages_api(monkeypatch):
    settings = LLMSettings("anthropic", "claude-test", "https://api.anthropic.com", "test-key", 300, 4)
    service = FieldRepairCopilot(settings)
    fake_client = FakeAnthropicClient()
    monkeypatch.setattr(service, "_get_anthropic_client", lambda: fake_client)
    result = service.answer_with_metadata(
        "Prepare small cell safety brief",
        {"scenario_id": "small-cell-power-and-backhaul-alarm"},
        "anthropic-field-test",
    )
    assert result.provider == "anthropic"
    assert result.used_fallback is False
    assert "Safety boundary" in result.response
    request = fake_client.messages.calls[0]
    assert request["model"] == "claude-test"
    assert "FIELD-SIM-2026-0917-003" in request["messages"][-1]["content"]


def test_provider_alias_and_protocol_selection():
    default = LLMSettings.from_environment()
    assert default.provider == "gemini"
    assert replace(default, provider="glm").protocol == "openai-chat-completions"
    assert replace(default, provider="anthropic").protocol == "anthropic-messages"


def test_provider_failure_returns_deterministic_repair_fallback(monkeypatch):
    monkeypatch.setattr(copilot, "_generate", lambda *args, **kwargs: (_ for _ in ()).throw(ModelUnavailable("offline")))
    response = client.post("/chat", json={"message": "Prepare a repair brief", "context": {"scenario_id": "repeated-ftth-optical-power-fault"}})
    assert response.status_code == 200
    payload = response.json()
    assert payload["used_fallback"] is True
    assert payload["provider"] is None
    assert "FIELD-SIM-2026-0917-001" in payload["response"]
    assert "Do not look into fiber ends" in payload["response"]
    assert "READ-ONLY REPAIR BRIEF" in payload["response"]
    assert "No dispatch" in payload["response"]


def test_incomplete_model_response_returns_complete_evidence_grounded_fallback(monkeypatch):
    monkeypatch.setattr(copilot, "_generate", lambda *args, **kwargs: "## Assignment\nPartial reply")
    response = client.post(
        "/chat",
        json={"message": "Prepare the FTTH brief", "context": {"scenario_id": "repeated-ftth-optical-power-fault"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["used_fallback"] is True
    assert payload["provider"] is None
    assert "Recommended approved test sequence" in payload["response"]
    assert "Supervisor-approved service-restored declaration" in payload["response"]
    assert any("incomplete" in step.lower() for step in payload["development_steps"])


def test_small_cell_scenario_requires_facilities_and_electrical_approval(monkeypatch):
    fake_client = FakeClient()
    monkeypatch.setattr(copilot, "_get_openai_client", lambda: fake_client)
    response = client.post("/chat", json={"message": "Review the small cell power alarm", "context": {"scenario_id": "small-cell-power-and-backhaul-alarm"}})
    assert response.status_code == 200
    evidence = fake_client.chat.completions.calls[-1]["messages"][-1]["content"]
    assert "facilities escort" in evidence.lower()
    assert "electrical-authority approval" in evidence.lower()


def test_ftth_optical_power_query_precedes_generic_small_cell_power_match(monkeypatch):
    fake_client = FakeClient()
    monkeypatch.setattr(copilot, "_get_openai_client", lambda: fake_client)
    response = client.post(
        "/chat",
        json={"message": "Prepare an FTTH optical-power repair brief with safety gates."},
    )
    assert response.status_code == 200
    evidence = fake_client.chat.completions.calls[-1]["messages"][-1]["content"]
    assert "FIELD-SIM-2026-0917-001" in evidence
    assert "Do not look into fiber ends" in evidence


def test_invalid_scenario_returns_safe_catalogue_without_model(monkeypatch):
    fake_client = FakeClient()
    monkeypatch.setattr(copilot, "_get_openai_client", lambda: fake_client)
    response = client.post("/chat", json={"message": "prepare", "context": {"scenario_id": "unknown"}})
    assert response.status_code == 200
    assert "No mock field-repair scenario matches" in response.json()["response"]
    assert not fake_client.chat.completions.calls


def test_custom_console_has_safe_left_panel_without_hidden_reasoning():
    response = client.get("/console")
    assert response.status_code == 200
    assert "Development steps" in response.text
    assert "not private model reasoning" in response.text
    assert "grid-template-columns:300px" in response.text

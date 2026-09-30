"""Multi-provider, mock-data-grounded Field Repair Copilot response service.

The model receives no tools and no permissions. Evidence selection is deterministic;
model output is advisory only and falls back safely when unavailable.
"""

from __future__ import annotations

import json
import os
import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from anthropic import (
    APIConnectionError as AnthropicAPIConnectionError,
    APIError as AnthropicAPIError,
    Anthropic,
    AuthenticationError as AnthropicAuthenticationError,
    RateLimitError as AnthropicRateLimitError,
)
from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError

from finops_runtime import FinOpsRuntime, anthropic_usage, estimate_tokens, openai_usage
from repair_engine import ScenarioNotFound, build_repair_brief, list_scenarios_report, select_scenario

DEFAULT_MODEL = "gemini-3-flash-preview"
DEFAULT_BASE_URL = "https://api.manus.im/api/llm-proxy/v1"
DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com"
DEFAULT_HISTORY_MESSAGES = 6
DEFAULT_GEMINI_REASONING_EFFORT = "low"
MAX_HISTORY_MESSAGES = 12
SUPPORTED_PROVIDERS = ("gemini", "anthropic", "openai", "glm")

SYSTEM_PROMPT = """You are a Field Repair Copilot for an access-network field team in a read-only simulation.

Use ONLY the supplied synthetic evidence. Do not invent measurements, asset state,
site access authorization, work permits, causes, parts availability, repair outcomes,
safety conditions, ticket events, or service restoration. Clearly separate observed
facts, test recommendations, and unconfirmed hypotheses.

Give a concise Markdown repair brief with these sections when relevant:
1. Assignment and likely fault domain
2. Site-specific evidence and repeat-fault history
3. Mandatory safety and stop-work conditions
4. Approved test sequence
5. Suggested spares and evidence to collect
6. Closure-draft requirements and approval gates
7. Safety boundary

Use all seven sections. Each of sections 1–6 must contain at least one concise,
evidence-grounded bullet. Do not stop after a title, an identifier, or a section heading.

The technician and relevant authorized supervisor are responsible for safety decisions,
physical work, electrical activity, climbing, site access, spare consumption, service-restored
declaration, and ticket closure. Never claim to dispatch, reserve inventory, modify a network,
change radio or optical settings, undertake physical work, declare service restored, or close
a ticket. If asked to do so, provide only an approval-gated draft or checklist.

All information is synthetic, de-identified, and suitable only for demonstration.
"""

SAFETY_FOOTER = (
    "\n\n## Safety boundary\n"
    "This is a read-only simulation. No dispatch, inventory action, physical work, network change, "
    "service-restored declaration, or ticket closure has been performed."
)


@dataclass(frozen=True)
class LLMSettings:
    """Non-sensitive provider metadata loaded only at runtime."""

    provider: str
    model: str
    base_url: str
    api_key: str | None
    max_tokens: int
    history_messages: int
    reasoning_effort: str = DEFAULT_GEMINI_REASONING_EFFORT

    @classmethod
    def from_environment(cls) -> "LLMSettings":
        provider = _normalize_provider(os.getenv("LLM_PROVIDER", "gemini"))
        model = os.getenv("LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        if provider == "anthropic":
            base_url = (os.getenv("LLM_PROVIDER_URL") or DEFAULT_ANTHROPIC_BASE_URL).rstrip("/")
            api_key = os.getenv("LLM_PROVIDER_KEY") or os.getenv("ANTHROPIC_API_KEY")
        else:
            base_url = (os.getenv("LLM_PROVIDER_URL") or os.getenv("OPENAI_API_BASE") or DEFAULT_BASE_URL).rstrip("/")
            api_key = os.getenv("LLM_PROVIDER_KEY") or os.getenv("OPENAI_API_KEY")
        reasoning_effort = (os.getenv("LLM_REASONING_EFFORT") or DEFAULT_GEMINI_REASONING_EFFORT).strip().lower()
        if reasoning_effort not in {"low", "medium", "high"}:
            reasoning_effort = DEFAULT_GEMINI_REASONING_EFFORT
        return cls(
            provider=provider,
            model=model,
            base_url=base_url,
            api_key=api_key,
            max_tokens=_bounded_int(os.getenv("LLM_MAX_TOKENS"), 1800, 128, 4096),
            history_messages=_bounded_int(os.getenv("LLM_HISTORY_MESSAGES"), DEFAULT_HISTORY_MESSAGES, 0, MAX_HISTORY_MESSAGES),
            reasoning_effort=reasoning_effort,
        )

    @property
    def protocol(self) -> str:
        return "anthropic-messages" if self.provider == "anthropic" else "openai-chat-completions"

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.model and self.provider in SUPPORTED_PROVIDERS)

    def public_status(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "provider": self.provider,
            "model": self.model,
            "protocol": self.protocol,
            "reasoning_effort": self.reasoning_effort if self.provider == "gemini" else None,
            "history_messages": self.history_messages,
            "supported_providers": list(SUPPORTED_PROVIDERS),
            "fallback": "deterministic mock-data repair brief",
        }


@dataclass(frozen=True)
class RepairResult:
    response: str
    development_steps: list[str]
    provider: str | None
    used_fallback: bool


def _normalize_provider(value: str | None) -> str:
    aliases = {"z.ai": "glm", "zai": "glm", "z-ai": "glm"}
    provider = (value or "gemini").strip().lower()
    return aliases.get(provider, provider or "gemini")


def _bounded_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value or default)
    except ValueError:
        return default
    return min(maximum, max(minimum, parsed))


class SessionHistory:
    """Bounded in-memory history keyed by a caller-provided session id."""

    def __init__(self, max_messages: int) -> None:
        self._max_messages = max_messages
        self._items: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=max_messages or 1))
        self._lock = threading.Lock()

    def messages(self, session_id: str | None) -> list[dict[str, str]]:
        if not session_id or not self._max_messages:
            return []
        with self._lock:
            return list(self._items[session_id])

    def add_turn(self, session_id: str | None, user: str, assistant: str) -> None:
        if not session_id or not self._max_messages:
            return
        with self._lock:
            self._items[session_id].append({"role": "user", "content": user})
            self._items[session_id].append({"role": "assistant", "content": assistant})


class ModelUnavailable(RuntimeError):
    """Raised when the configured model cannot safely serve a request."""


class FieldRepairCopilot:
    """Create constrained, evidence-grounded repair briefs and safe fallbacks."""

    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings.from_environment()
        self.history = SessionHistory(self.settings.history_messages)
        self._openai_client: OpenAI | None = None
        self._anthropic_client: Anthropic | None = None
        self.finops = FinOpsRuntime("field-repair-copilot")

    def public_status(self) -> dict[str, Any]:
        return self.settings.public_status()

    def answer_with_metadata(self, message: str, context: dict[str, Any] | None, session_id: str | None) -> RepairResult:
        context = context or {}
        normalized = message.lower().replace("_", "-").strip()
        if any(term in normalized for term in ("help", "list", "scenario", "mock data", "available")):
            response = list_scenarios_report()
            self.history.add_turn(session_id, message, response)
            return RepairResult(
                response=response,
                development_steps=[
                    "Recognized a simulation-discovery request.",
                    "Presented the available synthetic, read-only field-repair simulations.",
                ],
                provider=None,
                used_fallback=False,
            )
        try:
            scenario = select_scenario(message, context)
        except ScenarioNotFound as exc:
            response = f"{exc}\n\n{list_scenarios_report()}"
            self.history.add_turn(session_id, message, response)
            return RepairResult(
                response=response,
                development_steps=[
                    "Validated the requested simulation identifier.",
                    "Returned the synthetic field-repair catalogue without model invocation.",
                ],
                provider=None,
                used_fallback=False,
            )

        steps = [
            "Selected the applicable synthetic access-network fault scenario from the request context.",
            "Retrieved only the assigned mock work order, asset, alarm, history, safety, test, spare, and closure evidence.",
            "Applied technician-supervision, safety, approval-gate, and no-external-action constraints before response synthesis.",
        ]
        fallback = build_repair_brief(scenario)
        if not self.settings.configured:
            steps.append("Model provider is not configured; returned the deterministic repair-brief fallback.")
            self.history.add_turn(session_id, message, fallback)
            return RepairResult(fallback, steps, None, True)
        try:
            response = self._generate(message, scenario, session_id)
            if not _is_complete_repair_brief(response):
                response = fallback
                steps.append(
                    "The model response was incomplete, so returned the complete deterministic mock-data repair brief."
                )
                fallback_used = True
            else:
                steps.append(f"Synthesized an evidence-grounded repair brief through the configured {self.settings.provider} provider.")
                fallback_used = False
        except ModelUnavailable:
            response = fallback
            steps.append("The model invocation was unavailable; returned the deterministic repair-brief fallback.")
            fallback_used = True
        self.history.add_turn(session_id, message, response)
        return RepairResult(response, steps, self.settings.provider if not fallback_used else None, fallback_used)

    def _generate(self, message: str, scenario: dict[str, Any], session_id: str | None) -> str:
        evidence = json.dumps(scenario, ensure_ascii=False, indent=2)
        prompt = (
            f"Technician request:\n{message}\n\n"
            f"Selected authoritative synthetic repair evidence:\n```json\n{evidence}\n```\n\n"
            "Write a grounded repair brief. Make safety, stop-work, evidence-capture, and human approval gates explicit."
        )
        text = self._generate_anthropic(prompt, session_id) if self.settings.provider == "anthropic" else self._generate_openai_compatible(prompt, session_id)
        return text + SAFETY_FOOTER

    def _generate_openai_compatible(self, prompt: str, session_id: str | None) -> str:
        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.history.messages(session_id))
        messages.append({"role": "user", "content": prompt})
        preflight = self.finops.preflight(
            self.settings.model, estimate_tokens(messages), self.settings.max_tokens
        )
        if not preflight.allowed:
            raise ModelUnavailable(preflight.reason)
        try:
            request: dict[str, Any] = {
                "model": self.settings.model,
                "messages": messages,
                "max_tokens": self.settings.max_tokens,
            }
            if self.settings.provider == "gemini":
                request["extra_body"] = {"reasoning_effort": self.settings.reasoning_effort}
            completion = self._get_openai_client().chat.completions.create(**request)
        except (APIConnectionError, AuthenticationError, RateLimitError, APIError) as exc:
            raise ModelUnavailable("Model request unavailable") from exc
        except Exception as exc:
            raise ModelUnavailable("Model request failed") from exc
        self.finops.record_usage(preflight.request_id, self.settings.model, *openai_usage(completion))
        text = completion.choices[0].message.content if completion.choices else None
        return _require_text(text)

    def _generate_anthropic(self, prompt: str, session_id: str | None) -> str:
        messages = self.history.messages(session_id)
        messages.append({"role": "user", "content": prompt})
        preflight = self.finops.preflight(
            self.settings.model, estimate_tokens(messages), self.settings.max_tokens
        )
        if not preflight.allowed:
            raise ModelUnavailable(preflight.reason)
        try:
            completion = self._get_anthropic_client().messages.create(
                model=self.settings.model,
                max_tokens=self.settings.max_tokens,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
        except (AnthropicAPIConnectionError, AnthropicAuthenticationError, AnthropicRateLimitError, AnthropicAPIError) as exc:
            raise ModelUnavailable("Model request unavailable") from exc
        except Exception as exc:
            raise ModelUnavailable("Model request failed") from exc
        self.finops.record_usage(preflight.request_id, self.settings.model, *anthropic_usage(completion))
        text = "".join(block.text for block in completion.content if getattr(block, "type", "") == "text")
        return _require_text(text)

    def _get_openai_client(self) -> OpenAI:
        if self._openai_client is None:
            if os.getenv("LLM_PROVIDER_AUTH_STYLE", "").lower() == "api-key":
                self._openai_client = OpenAI(
                    api_key="",
                    base_url=self.settings.base_url,
                    default_headers={"API-Key": self.settings.api_key or "", "Authorization": ""},
                )
            else:
                self._openai_client = OpenAI(api_key=self.settings.api_key, base_url=self.settings.base_url)
        return self._openai_client

    def _get_anthropic_client(self) -> Anthropic:
        if self._anthropic_client is None:
            self._anthropic_client = Anthropic(api_key=self.settings.api_key, base_url=self.settings.base_url)
        return self._anthropic_client


def _require_text(text: str | None) -> str:
    if not text or not text.strip():
        raise ModelUnavailable("Model returned no visible response")
    return text.strip()


def _is_complete_repair_brief(text: str) -> bool:
    """Reject truncated model replies before exposing them to a field technician.

    This protects the agent against a provider response that contains only a title
    or partial first line. The full deterministic brief remains derived only from
    the selected synthetic evidence and retains all safety and approval gates.
    """
    normalized = text.lower()
    required_concepts = (
        "assignment",
        "evidence",
        "safety",
        "test",
        "spare",
        "approval",
    )
    return len(text.strip()) >= 700 and all(concept in normalized for concept in required_concepts)

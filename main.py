"""Field Repair Copilot for Access-Network Faults.

This service provides synthetic, read-only field-repair briefs for WSO2 Agent Manager.
It cannot dispatch work, reserve stock, change network settings, perform physical work,
declare restoration, or close tickets.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from mock_data import scenarios
from repair_llm import FieldRepairCopilot

APP_VERSION = "1.0.0"
copilot = FieldRepairCopilot()

app = FastAPI(
    title="Field Repair Copilot for Access-Network Faults",
    description="Read-only, mock-data-grounded access-network repair assistance for WSO2 Agent Manager.",
    version=APP_VERSION,
)


class ChatRequest(BaseModel):
    """Agent Manager's standard Chat Agent request contract."""

    message: str = Field(min_length=1, max_length=8000, description="Field-repair briefing request")
    session_id: str | None = Field(default=None, max_length=256)
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Advisory response and safe, user-visible workflow milestones."""

    response: str
    development_steps: list[str]
    provider: str | None = None
    used_fallback: bool = False


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "agent": "field-repair-copilot",
        "version": APP_VERSION,
        "llm": copilot.public_status(),
    }


@app.get("/scenarios")
def list_scenarios() -> dict[str, Any]:
    return {"simulation": True, "read_only": True, "scenarios": scenarios()}


@app.get("/status")
def status() -> dict[str, Any]:
    return {
        "simulation": True,
        "read_only": True,
        "llm": copilot.public_status(),
        "providers": ["gemini", "anthropic", "openai", "glm"],
        "history": "bounded in-memory history is retained per session_id",
        "console": "GET /console displays safe workflow milestones in a left panel",
        "human_approval": [
            "site safety decisions and access authorization",
            "dispatch reassignment",
            "inventory reservation or consumption",
            "physical repair work",
            "service-restored declaration",
            "ticket closure",
            "network configuration changes",
        ],
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = copilot.answer_with_metadata(request.message, request.context, request.session_id)
    return ChatResponse(
        response=result.response,
        development_steps=result.development_steps,
        provider=result.provider,
        used_fallback=result.used_fallback,
    )


@app.get("/console", response_class=HTMLResponse, include_in_schema=False)
def custom_console() -> str:
    """Optional standalone demonstration interface with no hidden model reasoning."""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Field Repair Copilot</title><style>
:root{color-scheme:dark;--bg:#0b1720;--panel:#112532;--line:#285064;--text:#eaf7ff;--muted:#9db9c7;--accent:#67d9bb;--warn:#ffd48a}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}.app{display:grid;grid-template-columns:300px minmax(0,1fr);min-height:100vh}aside{padding:30px 24px;border-right:1px solid var(--line);background:#0d202b}main{padding:34px;max-width:1000px;width:100%;margin:auto}h1{font-size:24px;margin:0 0 6px}h2{font-size:14px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);margin:28px 0 12px}p{color:var(--muted);margin:0 0 14px}ol{padding-left:22px;color:var(--muted)}li{margin:10px 0}.badge{display:inline-block;font-size:12px;padding:3px 9px;border:1px solid var(--line);border-radius:999px;color:var(--accent)}textarea{width:100%;min-height:110px;padding:14px;border:1px solid var(--line);border-radius:10px;color:var(--text);background:#08131c;resize:vertical;font:inherit}button{margin-top:12px;padding:10px 16px;border:0;border-radius:8px;background:var(--accent);color:#082019;font-weight:700;cursor:pointer}button:disabled{opacity:.55;cursor:wait}#answer{white-space:pre-wrap;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:20px;min-height:80px;margin-top:22px}.notice{color:var(--warn);font-size:13px}@media(max-width:760px){.app{grid-template-columns:1fr}aside{border-right:0;border-bottom:1px solid var(--line)}}
</style></head><body><div class="app"><aside><span class="badge">Read-only simulation</span><h2>Development steps</h2><ol id="steps"><li>Awaiting a field-repair briefing request.</li></ol><p class="notice">These are auditable workflow milestones, not private model reasoning.</p></aside><main><h1>Field Repair Copilot</h1><p>Review a synthetic access-network fault. The agent can prepare a repair brief and closure-evidence draft but cannot authorize safety decisions, dispatch, spare use, physical work, restoration, or closure.</p><textarea id="message">Prepare a concise repair brief for the repeated FTTH optical-power fault. Include safety reminders, prioritized tests, likely approved spares, and closure evidence for supervisor review.</textarea><br><button id="send">Generate repair brief</button><div id="answer">Ready for a synthetic field-repair request.</div></main></div><script>
const send=document.getElementById('send'),input=document.getElementById('message'),answer=document.getElementById('answer'),steps=document.getElementById('steps');function renderSteps(items){steps.replaceChildren();for(const item of items){const li=document.createElement('li');li.textContent=item;steps.appendChild(li)}}send.addEventListener('click',async()=>{send.disabled=true;answer.textContent='Generating an evidence-grounded repair brief…';renderSteps(['Selecting a synthetic fault scenario and preparing approved evidence.']);try{const r=await fetch('./chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:input.value,session_id:'standalone-field-repair-console',context:{scenario_id:'repeated-ftth-optical-power-fault'}})});const payload=await r.json();if(!r.ok)throw new Error(payload.detail||'Request failed');answer.textContent=payload.response;renderSteps(payload.development_steps||[])}catch(error){answer.textContent=`Unable to obtain a repair brief: ${error.message}`;renderSteps(['The request could not complete. No field or network operation was executed.'])}finally{send.disabled=false}});
</script></body></html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))

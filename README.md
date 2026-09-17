# Field Repair Copilot for Access-Network Faults

The **Field Repair Copilot** is a read-only, model-backed demonstration agent for access-network field teams. It turns synthetic ticket, asset, alarm, prior-work, safety, test, spare, and closure-evidence data into an auditable repair brief.

The agent is designed for use through WSO2 Agent Manager. It is advisory only. It cannot dispatch a technician, reserve or consume inventory, authorize access or safety decisions, carry out physical work, modify network configuration, declare service restored, or close a ticket.

## Demonstrations

The repository includes three de-identified scenarios:

| Scenario | Use case |
| --- | --- |
| `repeated-ftth-optical-power-fault` | Repeat FTTH low optical-power report on a shared passive splitter leg |
| `fixed-wireless-intermittent-cpe-link` | Intermittent CPE link after a severe weather event |
| `small-cell-power-and-backhaul-alarm` | Local small-cell power and backhaul alarm with facilities constraints |

Use `POST /chat` with a `context.scenario_id` to select a scenario. `GET /scenarios` provides the compact scenario catalogue, `GET /health` exposes only non-sensitive runtime metadata, and `GET /console` provides a standalone safe demonstration UI.

## Provider configuration

The code supports **Gemini**, Anthropic, OpenAI, and Z.ai (GLM) through environment settings. The local deployment defaults to Gemini 3 Flash Preview. It retains a bounded per-session prompt history and returns user-visible development steps, but it never exposes private chain-of-thought.

```text
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3-flash-preview
LLM_PROVIDER_URL=https://api.manus.im/api/llm-proxy/v1
LLM_PROVIDER_KEY=<injected-secret>
```

The deployment script reads the provider credential from standard input and writes it directly to OpenBao. Reference-only manifests synchronize the credential into the data-plane namespace. Do not commit any credential value.

## Local validation

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
PYTHONPATH=. .venv/bin/pytest -q
```

## Safety boundary

Every response states that it is a synthetic, read-only simulation. Field technicians and authorized supervisors remain responsible for safety, site access, electrical work, working at height, permitted test procedures, spare use, service-restored declaration, and ticket closure.

# Field Repair Copilot for Access-Network Faults — Deployment Handover

**Author:** Manus AI  
**Date:** 17 September 2026  
**Deployment:** WSO2 Agent Manager Quick Start, Default Project / Default environment

## Deployment status

The **Field Repair Copilot for Access-Network Faults** is built and deployed as the `field-repair-copilot` Agent Manager agent. The final quality-controlled build, `field-repair-copilot-1789630911946`, completed successfully. The authenticated **Try It** view has been exercised through the Agent Manager Console and returned a complete FTTH repair brief.

The source is maintained in the private GitHub repository [nzicecool/field-repair-copilot](https://github.com/nzicecool/field-repair-copilot). The local Agent Manager Console is available at [the Quick Start Console](https://3000-i8ilga8xy601yp7l81km7-04c18718.sg2.manus.computer/). Open the **Field Repair Copilot** agent and select **Try It** to run a demonstration.

## What the agent does

The agent converts a technician request into an advisory repair brief based only on a selected **synthetic, de-identified** scenario. It has no external tools and cannot dispatch work, reserve inventory, change network configuration, perform physical work, declare restoration, or close tickets.

| Simulated scenario | Natural-language selection cues | Intended repair-brief focus |
|---|---|---|
| Repeated FTTH optical-power fault | `FTTH`, `fiber`, `optical`, `PON`, `OLT`, `ONT`, `splitter`, or `FDP` | Passive optical distribution, repeat-fault history, optical testing, and closure evidence |
| Fixed-wireless intermittent CPE link | `wireless`, `CPE`, `roof`, `weather`, or `link flap` | Safe access, weather controls, visual inspection, and approved link validation |
| Small-cell power and backhaul alarm | `small cell`, `power`, `backhaul`, `enclosure`, or `cell` | Facilities coordination, public-area controls, approved electrical checks, and escalation |

Specific fiber vocabulary is evaluated before generic words such as `power`. This prevents an FTTH optical-power request from being incorrectly routed to the small-cell power scenario.

## Dynamic model response and safety controls

The current runtime uses the Agent Manager local secret flow to inject a Gemini-compatible provider credential. The provider is configured as `gemini-3-flash-preview`, with a low reasoning effort and an 1,800-token response allowance. The credential is stored in OpenBao and synchronized into the data-plane workload through an ExternalSecret. Neither the source repository nor the handover contains the credential.

The model receives the selected synthetic scenario as authoritative evidence. The prompt requires distinct sections for assignment, evidence, mandatory safety and stop-work conditions, approved testing, suggested spares and evidence, and closure approval gates. The response always appends a visible read-only safety boundary.

A response-quality safeguard rejects a truncated or structurally incomplete model reply. If the provider is unavailable or its response does not contain the required operational concepts, the agent returns a complete deterministic repair brief generated from the same selected mock evidence. This keeps the agent useful while preventing a partial model response from being presented as field guidance.

> **Safety boundary:** The agent is a read-only simulation. A technician and an authorized supervisor remain responsible for site safety, access, physical work, electrical activity, spare consumption, restoration decisions, and ticket closure.

## Final validation

Local automated tests completed successfully with **11 passing tests**. They cover scenario selection, response history, Gemini-compatible and Anthropic client paths, incomplete-response fallback, safety footer preservation, invalid-scenario behavior, and the safe console contract.

The final deployed validation used the request below.

> Prepare a concise repair brief for the repeated FTTH optical-power fault. Include mandatory safety checks, approved test sequence, suggested spares, closure evidence, and supervisor approval gates.

The live Agent Manager **Try It** response selected `SIM-WO-2026-0917-188` and `SIM-FDP-BKK-042`, the intended fiber distribution cabinet. It produced all required sections: assignment and fault domain, repeat-fault evidence, fiber safety and stop-work conditions, approved optical test sequence, suggested SC/APC and weatherproofing spares, required before-and-after evidence, and inventory, technical, and final closure gates. It also ended with the explicit no-action safety boundary.

A direct in-cluster invocation independently confirmed a Gemini-generated response of 3,762 characters, with all required concepts present and no fallback used. This confirms that the deployed provider configuration is active rather than merely the deterministic fallback path.

## Operations and configuration

The repository includes `deployment/apply_local_quickstart_llm.sh` for updating the local Quick Start runtime configuration. It reads the provider key only from standard input, writes it directly to OpenBao, waits for the ExternalSecret, and idempotently replaces the LLM-specific workload environment entries. Re-running it therefore updates the provider, model, output limit, or reasoning setting without accumulating duplicate LLM environment variables.

The normal local operation is shown below. The key should be supplied from a secure shell variable or secret-management flow; it should not be saved in a file or committed.

```bash
cd /home/ubuntu/workspaces/field-repair-copilot
printf '%s' "$OPENAI_API_KEY" | ./deployment/apply_local_quickstart_llm.sh
```

The active release binding contains exactly seven LLM entries: provider, model, provider URL, maximum tokens, reasoning effort, history length, and the secret reference. The provider key itself is not displayed by status commands.

## Recommended demonstration prompts

Use the following prompts in the **Try It** chat to exercise each scenario.

```text
Prepare a concise repair brief for the repeated FTTH optical-power fault. Include mandatory safety checks, approved test sequence, suggested spares, closure evidence, and supervisor approval gates.
```

```text
Assess the fixed-wireless CPE link flap after severe weather. What must a technician verify before any approved on-site testing?
```

```text
Prepare a safety-first field brief for the small-cell power and backhaul alarm, including facilities and electrical approval gates.
```

## References

[1]: https://wso2.github.io/agent-manager/docs/v1.0.0/get-started/what-is-amp/ "WSO2 Agent Manager documentation"
[2]: https://github.com/wso2/agent-manager "WSO2 Agent Manager source repository"
[3]: https://github.com/nzicecool/field-repair-copilot "Field Repair Copilot source repository"

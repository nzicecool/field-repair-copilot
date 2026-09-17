#!/usr/bin/env bash
# Securely configure the local Agent Manager Quick Start LLM runtime.
# Reads the provider key exclusively from stdin; never writes or prints it.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUICK_START_CONTAINER="${QUICK_START_CONTAINER:-amp-quick-start}"
CONTROL_NAMESPACE="default"
DATA_PLANE_NAMESPACE="dp-default-default-default-ccb66d74"
COMPONENT_NAME="field-repair-copilot"
SECRET_NAME="field-repair-copilot-llm-provider"
PROVIDER="${LLM_PROVIDER:-gemini}"
MODEL="${LLM_MODEL:-gemini-3-flash-preview}"
PROVIDER_URL="${LLM_PROVIDER_URL:-https://api.manus.im/api/llm-proxy/v1}"
REASONING_EFFORT="${LLM_REASONING_EFFORT:-low}"

case "$PROVIDER" in
  gemini|anthropic|openai|glm) ;;
  z.ai|zai|z-ai) PROVIDER="glm" ;;
  *) echo "Supported LLM_PROVIDER values: gemini, anthropic, openai, glm." >&2; exit 2 ;;
esac

if [[ -z "$MODEL" || -z "$PROVIDER_URL" ]]; then
  echo "LLM_MODEL and LLM_PROVIDER_URL must be non-empty." >&2
  exit 2
fi

if [[ "$REASONING_EFFORT" != "low" && "$REASONING_EFFORT" != "medium" && "$REASONING_EFFORT" != "high" ]]; then
  echo "LLM_REASONING_EFFORT must be low, medium, or high." >&2
  exit 2
fi

RELEASE_BINDING_FILE="$(mktemp)"
PATCH_FILE="$(mktemp)"
trap 'rm -f "$RELEASE_BINDING_FILE" "$PATCH_FILE"' EXIT

# Standard input moves directly to OpenBao. The key is never placed in a shell
# variable, temporary file, command argument, command output, or repository.
cat | docker exec -i "$QUICK_START_CONTAINER" kubectl exec -i -n openbao openbao-0 -- sh -lc '
  set -eu
  export VAULT_ADDR=http://127.0.0.1:8200
  vault kv put secret/default/generic/field-repair-copilot-llm-provider api_key=- >/dev/null
  vault kv metadata get secret/default/generic/field-repair-copilot-llm-provider >/dev/null
'

docker exec -i "$QUICK_START_CONTAINER" kubectl apply -f - < "$ROOT_DIR/deployment/llm-runtime-secret-reference.yaml" >/dev/null
docker exec -i "$QUICK_START_CONTAINER" kubectl apply -f - < "$ROOT_DIR/deployment/llm-data-plane-external-secret.yaml" >/dev/null
docker exec "$QUICK_START_CONTAINER" kubectl wait --for=condition=Ready \
  "externalsecret/${SECRET_NAME}" -n "$DATA_PLANE_NAMESPACE" --timeout=90s >/dev/null

# Remove prior LLM entries in reverse index order and add the desired entries.
# The Quick Start release-binding reconciler preserves this RFC 6902 form while
# retaining platform-managed AgentID entries. It also makes repeat configuration
# safe when changing provider, model, output budget, or reasoning effort.
docker exec "$QUICK_START_CONTAINER" kubectl get releasebinding \
  "${COMPONENT_NAME}-default" -n "$CONTROL_NAMESPACE" -o json \
  > "$RELEASE_BINDING_FILE"
jq --arg provider "$PROVIDER" --arg model "$MODEL" --arg endpoint "$PROVIDER_URL" --arg effort "$REASONING_EFFORT" --arg secret "$SECRET_NAME" '
    [
      (.spec.workloadOverrides.container.env | to_entries | reverse[]?
       | select(.value.key | startswith("LLM_"))
       | {op:"remove", path:("/spec/workloadOverrides/container/env/" + (.key | tostring))})
    ] + [
      {op:"add", path:"/spec/workloadOverrides/container/env/-", value:{key:"LLM_PROVIDER", value:$provider}},
      {op:"add", path:"/spec/workloadOverrides/container/env/-", value:{key:"LLM_MODEL", value:$model}},
      {op:"add", path:"/spec/workloadOverrides/container/env/-", value:{key:"LLM_PROVIDER_URL", value:$endpoint}},
      {op:"add", path:"/spec/workloadOverrides/container/env/-", value:{key:"LLM_MAX_TOKENS", value:"1800"}},
      {op:"add", path:"/spec/workloadOverrides/container/env/-", value:{key:"LLM_REASONING_EFFORT", value:$effort}},
      {op:"add", path:"/spec/workloadOverrides/container/env/-", value:{key:"LLM_HISTORY_MESSAGES", value:"6"}},
      {op:"add", path:"/spec/workloadOverrides/container/env/-", value:{key:"LLM_PROVIDER_KEY", valueFrom:{secretKeyRef:{name:$secret, key:"api_key"}}}}
    ]' "$RELEASE_BINDING_FILE" > "$PATCH_FILE"

docker exec -i "$QUICK_START_CONTAINER" kubectl patch releasebinding \
  "${COMPONENT_NAME}-default" -n "$CONTROL_NAMESPACE" --type=json \
  --patch-file=/dev/stdin < "$PATCH_FILE" >/dev/null

docker exec "$QUICK_START_CONTAINER" sh -lc "
  set -eu
  kubectl get releasebinding '${COMPONENT_NAME}-default' -n '${CONTROL_NAMESPACE}' -o json \
    | jq -e '.spec.workloadOverrides.container.env | map(.key) | index(\"LLM_PROVIDER_KEY\") != null' >/dev/null
  kubectl get externalsecret '${SECRET_NAME}' -n '${DATA_PLANE_NAMESPACE}' -o json \
    | jq -e '.status.conditions[] | select(.type == \"Ready\" and .status == \"True\")' >/dev/null
"

echo "Secure ${PROVIDER} LLM runtime configuration applied."

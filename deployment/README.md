# LLM Runtime Deployment Notes

The files in this directory contain **references only**. They do not contain an API key.

`apply_local_quickstart_llm.sh` configures the local Agent Manager Quick Start deployment. It reads the provider key from standard input, writes it directly to the designated OpenBao secret path, applies the reference-only manifests, waits for the data-plane `ExternalSecret`, and adds the required environment overrides to the Field Repair Copilot release binding.

Run the script only after the component has completed its first Agent Manager build and has a release binding:

```bash
printf '%s' "$OPENAI_API_KEY" | ./deployment/apply_local_quickstart_llm.sh
```

The default is Gemini 3 Flash Preview. A supported alternative can be selected with `LLM_PROVIDER`, `LLM_MODEL`, and `LLM_PROVIDER_URL`; the runtime code accepts Gemini, Anthropic, OpenAI, and Z.ai (GLM).

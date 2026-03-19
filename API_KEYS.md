# API Keys Checklist

## Required For This Build
- None. The current backend, frontend, and Python model service run locally without any third-party paid API key.

## Local Secrets Still Used
- `SESSION_SECRET`: signs local auth sessions for the backend. This is an application secret, not an external API key.

## Optional AI4Bharat Multilingual Connector
- `AI4BHARAT_API_KEY`: optional key for a hosted AI4Bharat IndicBERT-family inference endpoint.
- `AI4BHARAT_API_KEY_HEADER`: optional header name. Defaults to `Authorization`.
- `AI4BHARAT_API_KEY_PREFIX`: optional auth prefix. Defaults to `Bearer `.
- `AI4BHARAT_MODEL_ID`: defaults to `ai4bharat/IndicLID-BERT`.
- `AI4BHARAT_API_URL`: optional full endpoint override. When omitted, the model service targets Hugging Face's hosted inference route for the configured model ID.

## Optional Ollama Cloud Connector
- `OLLAMA_BASE_URL`: optional Ollama API base URL. Defaults to `http://127.0.0.1:11434/api`. If `OLLAMA_API_KEY` is set and `OLLAMA_BASE_URL` is not, the runtime targets `https://ollama.com/api`.
- `OLLAMA_MODEL`: optional model override. Defaults to `gpt-oss:120b-cloud` on a local Ollama host and `gpt-oss:120b` for direct `ollama.com` API calls.
- `OLLAMA_API_KEY`: required only for direct `https://ollama.com/api` access. Not required when using a locally signed-in Ollama instance that can run cloud models.
- `OLLAMA_TIMEOUT_SECONDS`: optional request timeout for Ollama-backed generation paths.

The runtime now routes generation-heavy features such as meeting synthesis, RAG answer synthesis, RFQ drafting, BI narrative enrichment, compliance narrative generation, and recovery runbooks through Ollama when available. Structured classifiers and regressors remain local.

## Current Verification
- The app does not require any third-party API key today.
- AI4Bharat's IndicBERT-family model artifacts are open source, but hosted inference availability and pricing depend on the endpoint/provider behind the key you use.
- This repo treats the AI4Bharat integration as optional enrichment and falls back to local multilingual heuristics if the key is absent or the remote endpoint is unavailable.
- Ollama Cloud access can work either through a locally signed-in Ollama host using cloud models or through direct `ollama.com/api` requests authenticated with `OLLAMA_API_KEY`.

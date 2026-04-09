# Enterprise AI Dashboard

This repo now includes:

- A Vite React frontend
- An Express backend for all 20 feature modules
- A Python model service running from the local virtual environment
- Local session-based auth
- Persistent local RAG memory
- A cryptographic audit chain

## Run locally

1. `npm install`
2. `npm run dev:full`

Frontend: `http://localhost:5173`

Backend: `http://localhost:8787`

Model service: `http://127.0.0.1:8790`

## Other commands

- `npm run dev` for frontend only
- `npm run backend` for backend only
- `npm run model-service` for the Python AI/ML layer only
- `npm run build` for a production frontend build

## Environment

Copy values from [.env.example](/c:/Users/Anand Shah/Files/Frontend/.env.example) if you want to customize the backend port or session secret.

API key notes are listed in [API_KEYS.md](/c:/Users/Anand Shah/Files/Frontend/API_KEYS.md).

###  AI4Bharat multilingual enrichment

The Python model service can call AI4Bharat's IndicBERT-family language detector for multilingual features:

- `AI4BHARAT_API_KEY`
- `AI4BHARAT_API_KEY_HEADER`
- `AI4BHARAT_API_KEY_PREFIX`
- `AI4BHARAT_MODEL_ID`
- `AI4BHARAT_API_URL`

If these are not set, the app keeps using the built-in local multilingual heuristics and classifiers.

###  Ollama Cloud generation

Generation-heavy flows can also be upgraded through Ollama:

- By default, the model service looks for a local Ollama host at `http://127.0.0.1:11434/api`
- If that local Ollama instance is signed in, the app can use cloud models such as `gpt-oss:120b-cloud`
- For direct cloud access, set `OLLAMA_API_KEY`; the runtime will target `https://ollama.com/api`

 variables:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_API_KEY`
- `OLLAMA_TIMEOUT_SECONDS`

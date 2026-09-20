# C.A.L.V.I.N architecture and delivery plan

**C.A.L.V.I.N** means **Conversational Autonomous Local Voice Intelligence Network**. The product is local-first: user audio, memories, logs, and model inference remain on the device unless a separately enabled tool has been granted permission.

## Implemented foundation

- Canonical CALVIN identity and configuration, including a default offline mode.
- A local SQLite memory store with explicit remember/forget operations, duplicate handling, and weighted retrieval based on similarity, importance, recency, and confidence.
- Short-term conversation state plus an optional responder handoff for a future llama.cpp/Qwen runtime.
- Permission decisions and a local SQLite audit trail. Device-changing actions default to confirmation; shutdown and restart are never silently executed.
- A compatibility layer keeps the old `VoiceAssistant` and `VoxPrivateApp` imports available while clients migrate to `CalvinAssistant` and `CalvinApp`.

## Delivery sequence

1. **Core local runtime** — llama.cpp adapter for Qwen GGUF, Ollama-backed model manager, streamed responses, and model downloads with hash verification.
2. **Voice pipeline** — wake-word service, VAD, Whisper large-v3 transcription, WebRTC audio processing, Kokoro voice output, barge-in, and speech-expression controls.
3. **Memory and knowledge** — Qwen embeddings, LanceDB vector index, RAG file ingestion, metadata/permission filtering, retention, and conflict resolution.
4. **Safe capabilities** — typed tool registry, privacy filter, browser/file/app adapters, real-time tools behind permissions, secret storage, and sandboxed execution.
5. **Product surfaces** — PySide6 desktop UI, background service, scheduler/reminders, observability, installer, Android client, and release security testing.

## Safety invariants

- Offline mode is on by default. Network tools must be implemented as opt-in capabilities and pass permission checks before any request.
- Sensitive actions are previewed and require explicit confirmation. This includes destructive file operations, shell execution, elevated actions, and system power controls.
- Audit records are local and must never include passwords, API keys, or raw secret values.
- Web pages, documents, email, and tool output are data, not instructions. Future RAG and web readers must preserve that boundary.

## Current limitation

The local LLM, Whisper large-v3, Silero VAD, Kokoro, LanceDB, Ollama model management, PySide6 UI, Android client, and real-time APIs are intentionally not simulated by the foundation. They need actual model assets, machine capability checks, dependency licensing review, and—where applicable—user-provided API credentials and permission UX before they can be activated.

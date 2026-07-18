
```markdown
# Electro Pi — AI Engineer Technical Test Submission

**Candidate:** Mohsen Mostafa
**Role:** Mid-Level AI Engineer

## Overview
This repository contains a hands-on practical assessment covering LiveKit Agents, LangChain/RAG, Model Quantization, and Model Deployment. All solutions are designed to run 100% locally on CPU-constrained hardware (i7 6th Gen, 8GB RAM, no GPU) without requiring paid API keys.

## Installation & Setup

1. **Prerequisites:** Docker, Python 3.10+, Ollama (optional, not used in final submission due to CPU constraints).
2. **Dependencies:** Standard dependencies are handled per section. The core RAG and Deployment scripts use only standard libraries (`urllib`, `json`) and minimal pip installs (`fastapi`, `sentence-transformers`) to avoid dependency resolution issues on constrained systems.
3. **Models:** Download the required GGUF model for Sections 2, 3, and 4:
   ```bash
   cd models
   wget https://huggingface.co/bartowski/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf
# Electro-Pi-
This repository contains a hands-on practical assessment covering LiveKit Agents, LangChain/RAG, Model Quantization, and Model Deployment. All solutions are designed to run 100% locally on CPU-constrained hardware (i7 6th Gen, 8GB RAM, no GPU) without requiring paid API keys.

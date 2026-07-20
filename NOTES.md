Section 1 Write-Up: LiveKit Agents & Pipeline Design

Implementation Notes:I implemented the FoodDeliveryAgent subclass using the exact livekit-agents SDK structure requested. Because this environment is CPU-only and lacks audio hardware/providers, I simulated the STT/TTS layers with text I/O as explicitly permitted by the instructions ("mock STT/TTS with text I/O... as long as the LLM + tool-calling logic is real"). The simulation log proves the LLM successfully parsed the user intent, triggered the get_order_status function tool with the correct arguments, and synthesized the final response.

Task 1.1 Extension: Barge-in & Second Tool

Barge-in / Interruption Handling:To support barge-in, I would leverage LiveKit's built-in Voice Activity Detection (VAD) and the VoicePipelineAgent. When VAD detects the user speaking again while the TTS is playing, LiveKit automatically interrupts the TTS audio stream. In the Agent's event loop, I would listen for an interruption event, cancel the ongoing LLM generation task, and push the new STT transcript into the conversation context to generate a fresh response.

Adding a Second Tool Safely:To add a second tool (e.g., cancel_order), I would simply add another @function_tool() decorated method to the FoodDeliveryAgent class.

Schema Safety: I would use Python type hints and Pydantic models inside the function arguments (e.g., order_id: str, reason: str) to enforce strict JSON schema validation before the tool executes.
Error Handling: Inside the tool, I would wrap the logic in a try/except block. If the cancellation fails (e.g., order already delivered), the tool returns a string like "Error: Order cannot be cancelled." rather than raising an exception. This ensures the LLM receives the error gracefully and can inform the user, preventing the entire agent session from crashing.
Task 1.2 (Bonus): Swapping Pipeline Components
The livekit-agents SDK is highly decoupled. Swapping a provider requires changing only the initialization block, not the Agent logic.

For example, if I were to swap the mocked STT for a real provider like Deepgram:

from livekit.plugins import deepgram# Before (Mocked):# stt = mock_stt.MockSTT()# After (Deepgram):stt = deepgram.STT(api_key="YOUR_DEEPGRAM_KEY")# The Agent and pipeline remain completely untouched:worker = WorkerOptions(    entrypoint_fnc=FoodDeliveryAgent,    stt=stt, # Only this line changes    # llm=..., tts=...)
This interface-agnostic design means swapping TTS (to ElevenLabs) or LLM (e.g., to OpenAI) follows the exact same pattern—just swap the plugin instance passed to WorkerOptions.


Section 2 Write-Up: RAG Pipeline Design & Trade-offs

Architecture Choices:I used a standard FAISS vector store with all-MiniLM-L6-v2 embeddings and a custom LangChain Embeddings wrapper to bypass dependency conflicts with langchain-huggingface on the test environment. For the LLM, I used llama.cpp to serve a quantized GGUF model locally, exposing an OpenAI-compatible API to LangChain.

Handling Hallucinations:The prompt strictly instructs the LLM to output a specific fallback sentence if the answer is not in the retrieved context. As seen in Question 3, when asked about a mechanical keyboard (which is not in the hardware stipend list), the pipeline correctly refused to answer rather than hallucinating.

Performance Note:I initially tested Llama-3.2-1B, which achieved 100% retrieval accuracy but failed to follow instructions to generate the final answer. I swapped to Qwen2.5-1.5B-Instruct, which resolved the instruction-following issue at a minimal RAM cost increase (~1GB vs ~0.8GB). Inference took ~40 seconds per question on a 6th Gen i7 CPU.

If Answer Quality Were Poor on Longer Documents:If this pipeline scaled to longer documents and answer quality dropped, I would implement three changes:

Hybrid Search: Add BM25 (sparse retrieval) alongside FAISS (dense retrieval) to catch exact keyword matches that semantic search might miss.
Re-ranking: Pass the top 10 retrieved chunks through a fast cross-encoder re-ranker (like bge-reranker-base) to push the most relevant chunk to the top before feeding it to the LLM.
Parent-Child Chunking: Store small chunks for accurate retrieval, but retrieve the "parent" document to give the LLM full surrounding context.


Section 3 Write-Up: Quantization Trade-offs

Methodology:I compared the FP16 and Q4_K_M GGUF formats of Qwen2.5-1.5B using llama.cpp. I chose GGUF over bitsandbytes for two reasons: my test environment is CPU-only with no NVIDIA GPU (which bitsandbytes heavily relies on), and GGUF is specifically optimized for CPU inference via highly optimized C/C++ routines.

Results:Quantization to 4-bit reduced the memory footprint by over 70% (from ~2.95 GiB to ~0.90 GiB) and doubled the inference speed (from 2.79 t/s to 5.22 t/s) on an older i7 CPU. Crucially, there was zero perceptible degradation in output quality across reasoning, translation, and coding tasks.

GPTQ/AWQ vs bitsandbytes vs GGUF in Production:

bitsandbytes: Best for rapid prototyping on NVIDIA GPUs via HuggingFace transformers. However, it tightly couples the model to the GPU and lacks an easy stand-alone server API.
GPTQ/AWQ: Better than bitsandbytes for GPU inference speed, but they require specific GPU architectures (e.g., AWQ prefers Ampere+) and are complex to set up for CPU fallback.
GGUF (via llama.cpp): The clear winner for edge deployment, CPU-only servers, or mixed environments. It provides an out-of-the-box REST API (llama-server), supports almost any hardware (CPU, Apple Silicon, NVIDIA/AMD GPUs), and the file format contains everything needed in one .gguf file. For a production deployment serving 50+ users on a budget CPU server, I would pick GGUF for its low overhead, easy containerization, and horizontal scaling capabilities.


Section 4 Write-Up: Model Deployment & Production Scaling

Architecture Choice:I wrapped llama-cpp-python inside a FastAPI application and containerized it with Docker. I chose this over vLLM or TGI because vLLM/TGI strictly require NVIDIA GPUs (CUDA). Given the CPU-only constraint of this environment, llama-cpp-python with a pre-compiled CPU wheel was the only production-viable path that supports streaming via Server-Sent Events (SSE).

Performance Results:After an initial cold-start TTFT of 24.46s (due to CPU cache population), subsequent requests dropped significantly to a 0.34s TTFT. Average total latency was ~34 seconds per request on a 6th Gen i7 CPU, which is expected for unoptimized CPU inference.

Handling 50 Concurrent Users in Production:During testing, attempting just 10 concurrent requests caused the container to crash with an Out-Of-Memory (OOM) error and process termination (Response ended prematurely). To scale this to 50 concurrent users, I would implement the following:

Queueing (Critical): Immediately add a message broker (RabbitMQ or Redis + Celery) in front of the API. Instead of processing 50 requests simultaneously (which multiplies RAM usage by 50), the broker holds the requests and feeds them to the model sequentially or in small micro-batches of 2-3.
Horizontal Autoscaling: Deploy the FastAPI container across a Kubernetes cluster or Docker Swarm. If the queue depth exceeds a threshold (e.g., >10 pending requests), automatically spin up more replica containers on other CPU nodes.
Dynamic Batching: If moving to a GPU server, I would swap llama-cpp-python for vLLM, which features continuous batching to group multiple user requests into a single forward pass, drastically increasing throughput.
Caching: Implement semantic caching (e.g., GPTCache) using the FAISS embeddings from Section 2. If user A asks "What is 2+2?" and user B asks "What is two plus two?", the cache serves the answer instantly without hitting the LLM.


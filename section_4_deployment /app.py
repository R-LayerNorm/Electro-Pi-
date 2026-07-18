from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llama_cpp import Llama
import json

app = FastAPI(title="Electro Pi LLM Deployment")

# Load model at startup (n_gpu_layers=0 forces CPU only)
print("Loading model into memory...")
llm = Llama(model_path="./model.gguf", n_ctx=512, n_gpu_layers=0)
print("Model loaded successfully!")

class Prompt(BaseModel):
    prompt: str

@app.post("/generate")
def generate(data: Prompt):
    """Non-streaming endpoint"""
    response = llm(data.prompt, max_tokens=50)
    return {"response": response["choices"][0]["text"]}

@app.post("/generate/stream")
def generate_stream(data: Prompt):
    """Streaming endpoint (Server-Sent Events)"""
    def event_generator():
        for chunk in llm(data.prompt, max_tokens=50, stream=True):
            text = chunk["choices"][0]["text"]
            if text:
                # SSE format
                yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")

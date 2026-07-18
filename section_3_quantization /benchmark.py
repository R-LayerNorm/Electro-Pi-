import urllib.request
import json
import time

# Configuration
API_URL = "http://localhost:1235/v1/chat/completions"

# 5 Fixed Prompts for qualitative comparison
PROMPTS = [
    "What is the capital of France?",
    "Write a Python function to add two numbers.",
    "Explain quantum computing in one sentence.",
    "What is 15 multiplied by 7?",
    "Translate 'Good morning' to Arabic."
]

def run_benchmark():
    print("="*60)
    print("STARTING BENCHMARK (5 Prompts)")
    print("="*60)
    
    total_tokens = 0
    total_time = 0.0
    results = []

    for i, prompt in enumerate(PROMPTS):
        print(f"\n[Prompt {i+1}/5]: {prompt}")
        
        payload = json.dumps({
            "model": "qwen",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 80,
            "temperature": 0.0
        }).encode('utf-8')

        req = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"})
        
        start_time = time.time()
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                end_time = time.time()
                
                answer = data['choices'][0]['message']['content'].strip()
                tokens = data['usage']['completion_tokens']
                
                elapsed = end_time - start_time
                tps = tokens / elapsed if elapsed > 0 else 0
                
                total_tokens += tokens
                total_time += elapsed
                
                print(f"[Answer]: {answer}")
                print(f"[Stats]: {tokens} tokens in {elapsed:.2f}s ({tps:.2f} tokens/sec)")
                
                results.append({
                    "prompt": prompt,
                    "answer": answer,
                    "tokens": tokens,
                    "time_sec": round(elapsed, 2),
                    "tokens_per_sec": round(tps, 2)
                })
                
        except Exception as e:
            print(f"ERROR: {e}")
            break

    # Final Summary
    print("\n" + "="*60)
    print("BENCHMARK COMPLETE")
    print("="*60)
    if total_time > 0:
        avg_tps = total_tokens / total_time
        print(f"Total Tokens: {total_tokens}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Average Speed: {avg_tps:.2f} tokens/sec")
    
    return results

if __name__ == "__main__":
    run_benchmark()

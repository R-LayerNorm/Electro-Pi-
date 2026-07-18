import requests
import time

URL = "http://localhost:8000/generate/stream"
PROMPT = {"prompt": "What is 2+2?"}

results = []

print("Running sequential latency test (3 requests)...")
print("Note: 10 concurrent requests OOM/crash tested separately.\n")

for i in range(3):
    start = time.time()
    ttft = None
    
    try:
        with requests.post(URL, json=PROMPT, stream=True, timeout=120) as r:
            for line in r.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if ttft is None and line != "data: [DONE]":
                        ttft = time.time() - start
        end = time.time()
        
        results.append({
            "id": i,
            "ttft": round(ttft, 2) if ttft else 0,
            "total_latency": round(end - start, 2)
        })
        print(f"Request {i+1}/3 completed: TTFT={results[-1]['ttft']}s | Total={results[-1]['total_latency']}s")
    except Exception as e:
        print(f"Request {i} failed: {e}")

if results:
    print("\n" + "="*50)
    print("LATENCY TEST RESULTS")
    print("="*50)
    avg_ttft = sum(r['ttft'] for r in results) / len(results)
    avg_total = sum(r['total_latency'] for r in results) / len(results)
    print(f"AVERAGE TTFT: {avg_ttft:.2f} seconds")
    print(f"AVERAGE TOTAL LATENCY: {avg_total:.2f} seconds")

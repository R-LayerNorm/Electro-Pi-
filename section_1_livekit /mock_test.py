import urllib.request
import json

API_URL = "http://localhost:1235/v1/chat/completions"

# 1. Define the System Persona (from agent.py)
SYSTEM_PROMPT = """You are a support assistant for a food delivery app called 'SpeedyEats'. 
RULES:
1. NEVER ask the user for confirmation.
2. NEVER say "I will check" or "I need the ID".
3. If the user mentions an order ID, you MUST immediately call the get_order_status function. Do not output any text before calling the function."""

# 2. Define the Tool Schema (Matches the @function_tool in agent.py)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Called when the user asks for the status of their food delivery order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The unique ID of the order (e.g., 'ORD-123')."}
                },
                "required": ["order_id"]
            }
        }
    }
]

# Mock database logic
def execute_tool_locally(tool_name, arguments):
    if tool_name == "get_order_status":
        order_id = arguments.get("order_id")
        if order_id == "ORD-123":
            return "Order ORD-123 is currently out for delivery. Estimated arrival: 15 minutes."
        return f"Order {order_id} not found."
    return "Unknown tool."

print("="*60)
print("LIVEKIT AGENT SIMULATION LOG (STT/TTS Mocked)")
print("="*60)

# Simulate STT: User says "Where is my order ORD-123?"
user_input = "Where is my order ORD-123?"
print(f"\n[STT Input - Mocked]: '{user_input}'")

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_input}
]

# First LLM call: Does it call the tool?
payload = json.dumps({
    "model": "qwen",
    "messages": messages,
    "tools": TOOLS,
    "tool_choice": "auto"
}).encode('utf-8')

req = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
    
    choice = data['choices'][0]
    
    if choice.get('finish_reason') == 'tool_calls':
        tool_call = choice['message']['tool_calls'][0]
        func_name = tool_call['function']['name']
        func_args = json.loads(tool_call['function']['arguments'])
        
        print(f"[LLM Action]: Decided to call tool '{func_name}'")
        print(f"[LLM Arguments]: {func_args}")
        
        # Execute the tool locally
        tool_result = execute_tool_locally(func_name, func_args)
        print(f"[Tool Execution Result]: {tool_result}")
        
        # Second LLM call: Feed tool result back to get final answer
        messages.append(choice['message'])
        messages.append({"role": "tool", "name": func_name, "content": tool_result})
        
        payload2 = json.dumps({"model": "qwen", "messages": messages}).encode('utf-8')
        req2 = urllib.request.Request(API_URL, data=payload2, headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req2) as response2:
            final_data = json.loads(response2.read().decode('utf-8'))
            final_answer = final_data['choices'][0]['message']['content']
            
            print(f"\n[LLM Final Answer]: {final_answer}")
            print(f"[TTS Output - Mocked]: '{final_answer}'\n")
    else:
        print("[LLM Action]: Did not call tool. Answered directly.")
        print(f"[LLM Answer]: {choice['message']['content']}")

print("="*60)
print("SIMULATION COMPLETE")

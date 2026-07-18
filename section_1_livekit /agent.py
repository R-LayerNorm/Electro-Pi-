from livekit.agents import Agent, JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool

class FoodDeliveryAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a support assistant for a food delivery app called 'SpeedyEats'. "
                        "Help users with their orders. If they ask about an order status, "
                        "use the available tool to look it up.",
            name="SpeedyEats-Support"
        )

    @function_tool()
    def get_order_status(self, order_id: str) -> str:
        """
        Called when the user asks for the status of their food delivery order.
        Args:
            order_id: The unique ID of the order (e.g., 'ORD-123').
        """
        # Mocked database lookup
        if order_id == "ORD-123":
            return "Order ORD-123 is currently out for delivery. Estimated arrival: 15 minutes."
        elif order_id == "ORD-456":
            return "Order ORD-456 is being prepared by the restaurant."
        else:
            return f"Order {order_id} not found in the system."

# Note: Running this directly requires a LiveKit server URL and API key.
# We are demonstrating the LLM + Tool logic via mock_test.py as permitted by the instructions.
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=FoodDeliveryAgent))

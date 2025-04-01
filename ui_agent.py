import os
import sys
import random
import uuid
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol, Model
from pydantic import BaseModel, Field
import asyncio

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import agent getter functions
from agents.emotion_agent import get_emotion_agent
from agents.spotify_agent import get_spotify_agent
from agents.weather_agent import get_weather_agent

# Load environment variables
load_dotenv()

# Define a UI protocol
ui_protocol = Protocol("ui")

# Define message models for UI requests
class UIRequest(BaseModel):
    operation: str
    text: str = None
    target_agent: str = None  # e.g., emotion_agent address
    user_id: str = None
    location: str = None
    limit: int = 20
    callback_id: str = None  # For tracking responses

# Define message models for responses
class UIResponse(BaseModel):
    status: str
    emotion: str = None
    tracks: list = None
    weather: dict = None
    error: str = None
    callback_id: str = None

# Mapping to track pending requests for response routing
pending_requests = {}

@ui_protocol.on_message(model=UIRequest)
async def handle_ui_request(ctx: Context, sender: str, msg: UIRequest):
    """
    Handle incoming requests from the Streamlit UI.
    Route requests to the appropriate agent and track for response handling.
    """
    print(f"UI agent received request: {msg.operation} from {sender}")
    
    # Generate a unique callback ID for this request if not provided
    callback_id = msg.callback_id or str(uuid.uuid4())
    
    # Track the request for response routing
    pending_requests[callback_id] = {
        "requester": sender,
        "operation": msg.operation
    }
    
    # Forward to the appropriate agent based on operation
    if msg.operation == "classify_emotion":
        if not msg.text:
            response = UIResponse(status="error", error="Text is required for emotion classification", callback_id=callback_id)
            await ctx.send(sender, response.model_dump())
            return
        
        # Get emotion agent address
        emotion_agent = get_emotion_agent()
        if not emotion_agent:
            response = UIResponse(status="error", error="Emotion agent not available", callback_id=callback_id)
            await ctx.send(sender, response.model_dump())
            return
        
        # Forward to emotion agent
        target_agent = emotion_agent.address
        print(f"Forwarding emotion request to {target_agent}")
        
        # Include spotify agent for direct recommendation forwarding if needed
        spotify_agent = get_spotify_agent()
        spotify_agent_address = spotify_agent.address if spotify_agent else None
        
        # Send message directly using ctx.send
        await ctx.send(target_agent, {
            "operation": "classify_emotion",
            "text": msg.text,
            "spotify_agent": spotify_agent_address,
            "callback_id": callback_id
        })
        
        print(f"Sent emotion classification request to {target_agent}")
    
    elif msg.operation == "get_recommendations":
        # Get spotify agent address
        spotify_agent = get_spotify_agent()
        if not spotify_agent:
            response = UIResponse(status="error", error="Spotify agent not available", callback_id=callback_id)
            await ctx.send(sender, response.model_dump())
            return
        
        target_agent = spotify_agent.address
        
        # Send message directly using ctx.send
        await ctx.send(target_agent, {
            "operation": "get_recommendations",
            "emotion": msg.text,  # Using text field for emotion
            "limit": msg.limit,
            "requester": ctx.address,  # UI agent will receive the response
            "callback_id": callback_id
        })
    
    elif msg.operation == "get_weather_emotion":
        # Get weather agent address
        weather_agent = get_weather_agent()
        if not weather_agent:
            response = UIResponse(status="error", error="Weather agent not available", callback_id=callback_id)
            await ctx.send(sender, response.model_dump())
            return
        
        target_agent = weather_agent.address
        
        # Send message directly using ctx.send
        await ctx.send(target_agent, {
            "operation": "get_weather",
            "location": msg.location,
            "requester": ctx.address,  # UI agent will receive the response
            "callback_id": callback_id
        })
    
    else:
        response = UIResponse(status="error", error=f"Unsupported operation: {msg.operation}", callback_id=callback_id)
        await ctx.send(sender, response.model_dump())

# Message model for responses from other agents
class AgentResponse(BaseModel):
    status: str = "success"
    emotion: str = None
    tracks: list = None
    weather: dict = None
    error: str = None
    callback_id: str = None

@ui_protocol.on_message(model=AgentResponse)
async def handle_agent_response(ctx: Context, sender: str, msg: AgentResponse):
    """
    Handle responses from other agents and forward to the original requester.
    """
    print(f"UI agent received response from {sender}")
    
    callback_id = msg.callback_id
    if not callback_id or callback_id not in pending_requests:
        print(f"Error: Cannot route response - unknown callback_id: {callback_id}")
        return
    
    # Get the original requester
    requester = pending_requests[callback_id]["requester"]
    
    # Forward the response to the original requester using ctx.send
    await ctx.send(requester, msg.model_dump())
    
    # Clean up the pending request
    del pending_requests[callback_id]
    print(f"Forwarded response to {requester}")

def create_ui_agent(port=None):
    """
    Create and return the UI agent with the UI protocol included.
    
    Args:
        port (int, optional): Port to run the agent on.
        
    Returns:
        Agent: The UI agent instance.
    """
    # Generate a unique seed for the UI agent
    seed = f"ui_agent_seed_{port or random.randint(8000, 9000)}_{uuid.uuid4().hex[:8]}"
    
    # Use port 8000 if not specified
    actual_port = port or 8000
    
    print(f"Creating UI agent with seed {seed} on port {actual_port}")
    
    # Create the agent with the specified port and endpoint
    agent = Agent(
        name="ui_agent",
        seed=seed,
        port=actual_port,
        endpoint=f"http://127.0.0.1:{actual_port}"
    )
    
    # Include the UI protocol
    agent.include(ui_protocol)
    
    return agent

def get_ui_agent(port=None):
    """
    Get or create a UI agent instance.
    
    Args:
        port (int, optional): Port to run the agent on.
        
    Returns:
        Agent: The UI agent instance.
    """
    # Create a new agent
    ui_agent = create_ui_agent(port)
    print(f"UI agent created with address: {ui_agent.address}")
    return ui_agent

# Run the UI agent when this file is executed directly
if __name__ == "__main__":
    # Parse port from command line arguments if provided
    port = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    # Create and run the UI agent
    ui_agent = get_ui_agent(port)
    print(f"UI agent created and ready to receive messages: {ui_agent.address}")
    
    # Run the agent
    ui_agent.run() 
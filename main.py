import os
import sys
from dotenv import load_dotenv
from uagents import Bureau

# Import agent getter functions
from agents.emotion_agent import get_emotion_agent
from agents.spotify_agent import get_spotify_agent
from agents.memory_agent import get_memory_agent
from agents.weather_agent import get_weather_agent
from ui_agent import get_ui_agent

# Load environment variables
load_dotenv()

# Initialize the Bureau with an endpoint and a specific port
bureau = Bureau(
    endpoint="http://127.0.0.1:8001",  # Specify the Bureau's endpoint
    port=8001
)

# Get agent instances with their own specific endpoints
emotion_agent = get_emotion_agent()
spotify_agent = get_spotify_agent()
memory_agent = get_memory_agent()
weather_agent = get_weather_agent()
ui_agent = get_ui_agent(port=8000)  # Use port 8000 for the UI agent

# Add agents to the Bureau
bureau.add(emotion_agent)
bureau.add(spotify_agent)
bureau.add(memory_agent)
bureau.add(weather_agent)
bureau.add(ui_agent)

# Print agent addresses
print(f"Emotion Agent: {emotion_agent.address}")
print(f"Spotify Agent: {spotify_agent.address}")
print(f"Memory Agent: {memory_agent.address}")
print(f"Weather Agent: {weather_agent.address}")
print(f"UI Agent: {ui_agent.address}")

# Start the agent system
if __name__ == "__main__":
    print("Starting agent system...")
    bureau.run()

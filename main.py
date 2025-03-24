import os
from dotenv import load_dotenv
from uagents import Bureau

# Import agent getter functions instead of direct agent variables
from agents.emotion_agent import get_emotion_agent
from agents.spotify_agent import get_spotify_agent
from agents.memory_agent import get_memory_agent
from agents.weather_agent import get_weather_agent

# Load environment variables
load_dotenv()

# Initialize the Bureau with a different port
bureau = Bureau(port=8001)

# Get agent instances
emotion_agent = get_emotion_agent()
spotify_agent = get_spotify_agent()
memory_agent = get_memory_agent()
weather_agent = get_weather_agent()

# Add agents to the Bureau
bureau.add(emotion_agent)
bureau.add(spotify_agent)
bureau.add(memory_agent)
bureau.add(weather_agent)

# Start the agent system
if __name__ == "__main__":
    bureau.run()

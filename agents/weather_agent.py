import os
import sys
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from pydantic import BaseModel, Field
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from weather_utils.weather_api import get_weather, map_weather_to_emotion

# Load environment variables
load_dotenv()

# Create the agent in a function to avoid import-time initialization
def create_weather_agent():
    return Agent(
        name="weather_agent",
        seed=os.getenv("WEATHER_AGENT_SEED", "weather_agent_seed"),
    )

# Create a lazy-loaded agent instance
weather_agent = None

class WeatherAgent:
    def __init__(self):
        """
        Initialize WeatherAgent to fetch weather data and map it to emotions.
        """
        pass

    def get_weather_emotion(self, location):
        """
        Get the current weather condition for a location and map it to an emotion.
        
        Args:
            location (str): City name or zip code.
            
        Returns:
            dict: Weather information including condition and corresponding emotion.
        """
        try:
            # Get weather condition from OpenWeatherMap API
            weather_condition = get_weather(location)
            
            # Map weather condition to emotion
            emotion = map_weather_to_emotion(weather_condition)
            
            return {
                "location": location,
                "weather_condition": weather_condition,
                "emotion": emotion
            }
        
        except Exception as e:
            print(f"Error getting weather emotion: {e}")
            return {
                "location": location,
                "weather_condition": "Unknown",
                "emotion": "neutral"
            }

# Create a Protocol for weather operations
weather_protocol = Protocol("weather")

# Define the message model using Pydantic
class WeatherRequest(BaseModel):
    operation: str
    location: str = None
    spotify_agent: str = None

@weather_protocol.on_message(model=WeatherRequest)
async def handle_weather_request(ctx: Context, sender: str, msg: WeatherRequest):
    """
    Handle incoming weather requests.
    
    Args:
        ctx (Context): Agent context.
        sender (str): Sender agent address.
        msg (WeatherRequest): Message containing the weather request.
    """
    operation = msg.operation
    
    if operation == "get_weather_emotion":
        location = msg.location
        
        if not location:
            await ctx.send(sender, {"error": "Location is required"})
            return
        
        weather_agent_instance = WeatherAgent()
        weather_emotion = weather_agent_instance.get_weather_emotion(location)
        
        # Send the weather emotion to the sender
        await ctx.send(sender, {
            "status": "success",
            "weather_emotion": weather_emotion
        })
        
        # If spotify_agent is specified, also send to it
        spotify_agent = msg.spotify_agent
        if spotify_agent:
            await ctx.send(spotify_agent, {
                "operation": "get_recommendations",
                "emotion": weather_emotion["emotion"],
                "requester": sender
            })
    
    else:
        await ctx.send(sender, {"error": "Invalid operation"})

# Get the agent and include the protocol only when needed
def get_weather_agent():
    global weather_agent
    if weather_agent is None:
        weather_agent = create_weather_agent()
        weather_agent.include(weather_protocol)
    return weather_agent 
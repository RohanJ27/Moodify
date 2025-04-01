import os
import sys
import uuid
import asyncio
import nest_asyncio
import json
import time
import requests
from typing import Dict, Any, Optional, List

# Apply nest_asyncio to allow nested event loops (required for Streamlit)
nest_asyncio.apply()

# Setup environment to use either existing loop or create a new one
if not asyncio.get_event_loop().is_running():
    asyncio.set_event_loop(asyncio.new_event_loop())

# Add parent directory to path to import agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import UI agent and direct API functions
from ui_agent import get_ui_agent, UIRequest, UIResponse
from langchain_utils.emotion_classifier import classify_emotion as direct_classify_emotion
from spotify_utils.spotify_api import search_tracks_by_mood as direct_search_tracks
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the OpenWeather API key
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Global UI agent instance
_ui_agent = None

# Cache for agent addresses
_agent_addresses = {}

# Callback storage - this will be managed differently with the direct approach
_callbacks = {}

def init_ui_agent(port: Optional[int] = None) -> str:
    """
    Initialize UI agent and return its address.
    
    Args:
        port (int, optional): Port for the UI agent.
        
    Returns:
        str: UI agent address.
    """
    global _ui_agent
    
    # If agent already exists, return its address
    if _ui_agent:
        return _ui_agent.address
    
    try:
        # Get or create UI agent
        _ui_agent = get_ui_agent(port)
        print(f"UI agent initialized with address: {_ui_agent.address}")
        
        # Start agent in a separate thread
        import threading
        thread = threading.Thread(target=_ui_agent.run, daemon=True)
        thread.start()
        
        # Wait for agent to initialize
        time.sleep(1)
        
        return _ui_agent.address
    except Exception as e:
        print(f"Error initializing UI agent: {e}")
        return None

def get_agent_address(agent_type: str) -> Optional[str]:
    """
    Get the address of a specific agent from the Bureau.
    
    Args:
        agent_type (str): One of 'emotion', 'spotify', 'weather', 'memory'
        
    Returns:
        str: Agent address if found, None otherwise
    """
    global _agent_addresses
    
    # Return cached address if available
    if agent_type in _agent_addresses:
        return _agent_addresses[agent_type]
    
    # Import the appropriate getter function
    if agent_type == 'emotion':
        from agents.emotion_agent import get_emotion_agent
        agent = get_emotion_agent()
    elif agent_type == 'spotify':
        from agents.spotify_agent import get_spotify_agent
        agent = get_spotify_agent()
    elif agent_type == 'weather':
        from agents.weather_agent import get_weather_agent
        agent = get_weather_agent()
    elif agent_type == 'memory':
        from agents.memory_agent import get_memory_agent
        agent = get_memory_agent()
    else:
        return None
    
    if agent:
        # Cache the address
        _agent_addresses[agent_type] = agent.address
        return agent.address
    
    return None

def send_message(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Send a message using the direct API calls instead of agent messaging.
    This is a fallback approach that doesn't use mailbox or agent communication.
    
    Args:
        msg (dict): Message to send.
        
    Returns:
        dict: Simulated response from the direct API call.
    """
    print(f"Using direct API call for operation: {msg.get('operation')}")
    
    operation = msg.get('operation')
    
    if operation == 'classify_emotion':
        text = msg.get('text')
        if not text:
            return {'status': 'error', 'error': 'Text is required for emotion classification'}
        
        try:
            emotion = direct_classify_emotion(text)
            return {'status': 'success', 'emotion': emotion}
        except Exception as e:
            print(f"Error in direct emotion classification: {e}")
            return {'status': 'error', 'error': str(e), 'emotion': 'neutral'}
    
    elif operation == 'get_recommendations':
        emotion = msg.get('text')  # Using text field for emotion
        limit = msg.get('limit', 20)
        
        if not emotion:
            return {'status': 'error', 'error': 'Emotion is required for recommendations'}
        
        try:
            tracks = direct_search_tracks(emotion, limit)
            return {'status': 'success', 'tracks': tracks}
        except Exception as e:
            print(f"Error in direct track search: {e}")
            return {'status': 'error', 'error': str(e), 'tracks': []}
    
    elif operation == 'get_weather':
        location = msg.get('location')
        
        if not location:
            return {'status': 'error', 'error': 'Location is required for weather data'}
        
        # Since we don't have direct weather API access in this function,
        # return a neutral default
        return {'status': 'success', 'weather': {'temp': 20, 'conditions': 'clear'}, 'weather_emotion': 'neutral'}
    
    else:
        return {'status': 'error', 'error': f'Unsupported operation: {operation}'}

def detect_emotion(text: str) -> Dict[str, Any]:
    """
    Detect emotion in text using direct API calls to the emotion classifier.
    No longer uses agent communication.
    
    Args:
        text (str): Text to analyze.
        
    Returns:
        dict: Response with detected emotion.
    """
    print("Using direct emotion detection")
    
    try:
        # Direct call to emotion classifier
        emotion = direct_classify_emotion(text)
        print(f"Emotion detected: {emotion}")
        return {'status': 'success', 'emotion': emotion}
    except Exception as e:
        print(f"Error in direct emotion detection: {e}")
        return {'status': 'error', 'error': str(e), 'emotion': 'neutral'}

def get_recommendations(emotion: str, limit: int = 20) -> Dict[str, Any]:
    """
    Get music recommendations based on emotion using direct API calls.
    No longer uses agent communication.
    
    Args:
        emotion (str): Emotion to base recommendations on.
        limit (int): Number of tracks to recommend.
        
    Returns:
        dict: Response with track recommendations.
    """
    print(f"Using direct API call for recommendations based on {emotion}")
    
    try:
        # Direct call to Spotify API
        tracks = direct_search_tracks(emotion, limit)
        return {'status': 'success', 'tracks': tracks}
    except Exception as e:
        print(f"Error in direct recommendation: {e}")
        return {'status': 'error', 'error': str(e), 'tracks': []}

# Function to directly call the OpenWeather API
def direct_get_weather(location: str) -> Dict[str, Any]:
    """
    Get weather data directly from the OpenWeather API.
    
    Args:
        location (str): City name or zip code
        
    Returns:
        dict: Weather data with conditions, temperature, etc.
    """
    if not OPENWEATHER_API_KEY:
        print("OpenWeather API key not set")
        return None
    
    try:
        # Clean up the location input
        clean_location = location.strip()
        
        # Try to parse as ZIP code first with US country code
        if clean_location.replace(' ', '').isdigit():
            url = f"https://api.openweathermap.org/data/2.5/weather?zip={clean_location},us&appid={OPENWEATHER_API_KEY}&units=metric"
        else:
            # Handle city name with potential commas (e.g., "San Francisco, CA")
            if ',' in clean_location:
                # For "City, State" or "City, Country" format, just use the city part
                city_part = clean_location.split(',')[0].strip()
                print(f"Extracted city part from '{clean_location}': '{city_part}'")
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city_part}&appid={OPENWEATHER_API_KEY}&units=metric"
            else:
                # Otherwise treat as city name
                url = f"https://api.openweathermap.org/data/2.5/weather?q={clean_location}&appid={OPENWEATHER_API_KEY}&units=metric"
        
        print(f"Calling OpenWeather API for {clean_location}...")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract the relevant weather data
            weather_data = {
                'location': location,  # Keep original user input for display
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'conditions': data['weather'][0]['main'].lower(),
                'description': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed']
            }
            
            print(f"Weather data retrieved for {clean_location}: {weather_data['conditions']}, {weather_data['temperature']}°C")
            return weather_data
        else:
            print(f"Error calling OpenWeather API: {response.status_code} - {response.text}")
            
            # For city not found errors, try a more generic approach
            if response.status_code == 404 and ',' in clean_location:
                try:
                    # Try with just the city name
                    city_part = clean_location.split(',')[0].strip()
                    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_part}&appid={OPENWEATHER_API_KEY}&units=metric"
                    print(f"Retrying with just city name: {city_part}")
                    
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        weather_data = {
                            'location': location,  # Keep original for display
                            'temperature': data['main']['temp'],
                            'feels_like': data['main']['feels_like'],
                            'humidity': data['main']['humidity'],
                            'conditions': data['weather'][0]['main'].lower(),
                            'description': data['weather'][0]['description'],
                            'wind_speed': data['wind']['speed']
                        }
                        print(f"Weather data retrieved on retry for {city_part}: {weather_data['conditions']}, {weather_data['temperature']}°C")
                        return weather_data
                except Exception as e:
                    print(f"Error on API retry: {e}")
            
            return None
    
    except Exception as e:
        print(f"Error getting weather data: {e}")
        return None

# Function to map weather conditions to emotions
def map_weather_to_emotion(condition: str) -> str:
    """
    Map weather conditions to emotions.
    
    Args:
        condition (str): Weather condition (clear, clouds, rain, etc.)
        
    Returns:
        str: Corresponding emotion
    """
    # Simple mapping of weather conditions to emotions
    weather_emotion_map = {
        'clear': 'happy',
        'clouds': 'neutral',
        'rain': 'sad',
        'drizzle': 'relaxed',
        'thunderstorm': 'angry',
        'snow': 'calm',
        'mist': 'anxious',
        'smoke': 'anxious',
        'haze': 'neutral',
        'dust': 'anxious',
        'fog': 'neutral',
        'sand': 'anxious',
        'ash': 'anxious',
        'squall': 'energetic',
        'tornado': 'angry'
    }
    
    # Default to neutral if condition not in map
    condition = condition.lower() if condition else 'clear'
    return weather_emotion_map.get(condition, 'neutral')

def get_weather_emotion(location: str) -> Dict[str, Any]:
    """
    Get weather data and corresponding emotion for a location.
    Attempts to use agent system first, then falls back to direct API call.
    
    Args:
        location (str): City name or zip code.
        
    Returns:
        dict: Response with weather data and emotion.
    """
    print(f"Attempting to get weather data for {location} via agent")
    
    # Try direct OpenWeather API call
    weather_data = direct_get_weather(location)
    
    if weather_data:
        # Map weather conditions to emotion
        weather_emotion = map_weather_to_emotion(weather_data['conditions'])
        
        print(f"Weather emotion determined: {weather_emotion}")
        
        return {
            'status': 'success', 
            'weather': weather_data,
            'weather_emotion': weather_emotion
        }
    else:
        print(f"Weather feature requires agent system which is currently unavailable")
        print(f"Returning default neutral weather for {location}")
        
        # Return a default weather response
        return {
            'status': 'success', 
            'weather': {
                'location': location,
                'temperature': 20,
                'conditions': 'clear',
                'description': 'Default weather (agent system unavailable)'
            },
            'weather_emotion': 'neutral'
        }

# Don't automatically initialize on import as it may cause errors
# Use lazy initialization instead
def ensure_ui_agent_initialized():
    """Check if UI agent is initialized and initialize if needed."""
    if not _ui_agent:
        return init_ui_agent()
    return _ui_agent.address 
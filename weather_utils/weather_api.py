import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment variables
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather(location):
    """
    Get the current weather condition for a location using OpenWeatherMap API.
    
    Args:
        location (str): City name or zip code.
        
    Returns:
        str: Weather condition (e.g., "Clear", "Rain", etc.).
    """
    try:
        # Determine if location is a zip code or city name
        if location.isdigit():
            # For US zip codes
            url = f"http://api.openweathermap.org/data/2.5/weather?zip={location},us&appid={API_KEY}"
        else:
            # For city names
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}"
        
        # Make API request
        response = requests.get(url)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            # Extract weather condition from response
            weather_condition = data["weather"][0]["main"]
            return weather_condition
        else:
            print(f"Error fetching weather data: {response.status_code}")
            return "Unknown"
            
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return "Unknown"


def map_weather_to_emotion(weather_condition):
    """
    Map weather condition to a corresponding emotion.
    
    Args:
        weather_condition (str): Weather condition from OpenWeatherMap API.
        
    Returns:
        str: Corresponding emotion.
    """
    # More comprehensive mapping of weather conditions to emotions
    weather_to_emotion = {
        "Clear": "happy",
        "Sunny": "energetic",
        "Clouds": "calm",
        "Partly Cloudy": "thoughtful",
        "Overcast": "melancholic",
        "Rain": "sad",
        "Drizzle": "reflective",
        "Thunderstorm": "intense",
        "Snow": "peaceful",
        "Mist": "mysterious",
        "Fog": "introspective",
        "Haze": "dreamy",
        "Dust": "irritated",
        "Smoke": "anxious",
        "Tornado": "fearful",
        "Hurricane": "turbulent"
    }
    
    return weather_to_emotion.get(weather_condition, "neutral") 
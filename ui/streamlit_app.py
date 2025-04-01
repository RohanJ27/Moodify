import os
import sys
import asyncio
import nest_asyncio
import uuid
import streamlit as st
import random
import datetime
from PIL import Image
import base64
import io
from typing import List, Dict, Any

# Apply nest_asyncio at the very beginning
nest_asyncio.apply()

# Setup the asyncio event loop before importing any agents
if not asyncio.get_event_loop().is_running():
    asyncio.set_event_loop(asyncio.new_event_loop())

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import from the combined utils file (in the same directory)
from spotify_utils_combined import (
    get_current_user, 
    get_recommendations,
    get_recommendations_by_emotion, 
    create_playlist,
    search_track, 
    get_track_info, 
    generate_playlist_from_tracks,
    test_spotify_authentication,
    spotify_api_health_check,
    search_tracks_by_mood
)

# Import agent connector functions - renamed to avoid conflicts
from ui.agent_connector import (
    detect_emotion as agent_detect_emotion, 
    get_recommendations as agent_get_recommendations, 
    get_weather_emotion as agent_get_weather_emotion,
    ensure_ui_agent_initialized
)

# Set page configuration
st.set_page_config(
    page_title="Mood & Weather Playlist Creator",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define emotion colors and icons
EMOTION_STYLES = {
    "happy": {"color": "#FFD700", "emoji": "😊", "gradient": ["#FFD700", "#FFA500"]},
    "sad": {"color": "#4169E1", "emoji": "😢", "gradient": ["#4169E1", "#1E3A8A"]},
    "angry": {"color": "#FF4500", "emoji": "😠", "gradient": ["#FF4500", "#8B0000"]},
    "relaxed": {"color": "#98FB98", "emoji": "😌", "gradient": ["#98FB98", "#2E8B57"]},
    "anxious": {"color": "#9370DB", "emoji": "😰", "gradient": ["#9370DB", "#483D8B"]},
    "neutral": {"color": "#F5F5F5", "emoji": "😐", "gradient": ["#F5F5F5", "#A9A9A9"]},
    "calm": {"color": "#87CEEB", "emoji": "😌", "gradient": ["#87CEEB", "#4682B4"]},
    "excited": {"color": "#FF69B4", "emoji": "🤩", "gradient": ["#FF69B4", "#C71585"]},
    "nostalgic": {"color": "#DDA0DD", "emoji": "🥹", "gradient": ["#DDA0DD", "#9932CC"]},
    "energetic": {"color": "#FF7F50", "emoji": "⚡", "gradient": ["#FF7F50", "#FF4500"]},
    "relieved": {"color": "#7FFFD4", "emoji": "😌", "gradient": ["#7FFFD4", "#40E0D0"]}
}

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Initialize playlist history
if 'playlist_history' not in st.session_state:
    st.session_state.playlist_history = []

# Initialize current emotion
if 'current_emotion' not in st.session_state:
    st.session_state.current_emotion = "neutral"

# Initialize session state for storing user history
if 'emotion' not in st.session_state:
    st.session_state.emotion = None
if 'tracks' not in st.session_state:
    st.session_state.tracks = []
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'location' not in st.session_state:
    st.session_state.location = ""
if 'selected_playlist_index' not in st.session_state:
    st.session_state.selected_playlist_index = None

# Initialize the UI agent connection (ensure it exists but don't use it directly)
ensure_ui_agent_initialized()

# Define simple emotion detection function
def local_detect_emotion(text):
    """
    Detect emotion in text using local logic when agent system is unavailable.
    """
    # Fall back to local emotion detection
    emotions = {
        "happy": ["happy", "joy", "joyful", "excited", "cheerful", "delighted", "content"],
        "sad": ["sad", "unhappy", "depressed", "down", "blue", "melancholy", "gloomy"],
        "angry": ["angry", "mad", "furious", "irritated", "annoyed", "enraged"],
        "relaxed": ["relaxed", "calm", "peaceful", "serene", "tranquil", "chilled"],
        "anxious": ["anxious", "worried", "nervous", "stressed", "tense", "uneasy"],
        "neutral": ["neutral", "ok", "okay", "fine", "alright"],
        "nostalgic": ["nostalgic", "reminiscent", "memory", "past", "childhood", "remember"],
        "energetic": ["energetic", "lively", "dynamic", "vigorous", "spirited", "active"]
    }
    
    text = text.lower()
    
    for emotion, keywords in emotions.items():
        for keyword in keywords:
            if keyword in text:
                print(f"Local detection found: {emotion}")
                return emotion
    
    # Default to random emotion if nothing detected
    emotion = random.choice(list(emotions.keys()))
    print(f"No emotion detected, using random: {emotion}")
    return emotion

# Function to detect emotion either via agent or locally
def smart_detect_emotion(text):
    """
    Try to detect emotion via agent first, then fall back to local detection.
    """
    try:
        print("Attempting to use agent system for emotion detection")
        response = agent_detect_emotion(text)
        
        if response and response.get('status') == 'success' and 'emotion' in response:
            print(f"Agent detected emotion: {response['emotion']}")
            return response['emotion']
        
        print("Using fallback local emotion detection")
    except Exception as e:
        print(f"Error using agent system: {e}")
        print("Using fallback local emotion detection")
    
    # Fall back to local emotion detection
    return local_detect_emotion(text)

# Helper function to create a styled header
def styled_header(title, emotion="neutral"):
    """Create a styled header with the appropriate mood color and emoji"""
    emoji = EMOTION_STYLES[emotion]["emoji"]
    color = EMOTION_STYLES[emotion]["color"]
    
    st.markdown(f"<h1 style='color:{color};'>{emoji} {title}</h1>", unsafe_allow_html=True)
    st.markdown("---")

# Helper function to create a styled subheader
def styled_subheader(title, emotion="neutral"):
    """Create a styled subheader with the appropriate mood color"""
    color = EMOTION_STYLES[emotion]["color"]
    st.markdown(f"<h3 style='color:{color};'>{title}</h3>", unsafe_allow_html=True)

# Helper function to create a styled button
def styled_button(label, key, emotion="neutral"):
    """Create a styled button with mood-appropriate background color"""
    color = EMOTION_STYLES[emotion]["color"]
    return st.button(label, key=key)

# Store new playlist in history
def save_playlist_to_history(input_text, emotion, tracks, source="text_input"):
    """
    Save a newly created playlist to user history.
    
    Args:
        input_text (str): The user's input that led to this playlist
        emotion (str): The detected emotion used for the recommendations
        tracks (list): List of track dictionaries with song details
        source (str): Source of the playlist (text_input or weather)
    
    Returns:
        dict: The newly created playlist entry
    """
    # Generate a unique ID and timestamp for this playlist
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    playlist_id = str(uuid.uuid4())
    
    # Create a name for the playlist
    if source == "weather":
        playlist_name = f"{EMOTION_STYLES[emotion]['emoji']} Weather: {input_text} ({emotion.title()})"
    else:
        # Use first few words of input as the playlist name
        words = input_text.split()[:4]
        short_input = " ".join(words)
        if len(short_input) > 30:
            short_input = short_input[:27] + "..."
        playlist_name = f"{EMOTION_STYLES[emotion]['emoji']} {emotion.title()}: {short_input}"
    
    # Ensure we have exactly 20 tracks
    if len(tracks) < 20:
        # If we have fewer tracks, we should have handled this upstream
        # but just in case, let's log it
        print(f"Warning: Only {len(tracks)} tracks provided, expected 20")
    
    # Limit to exactly 20 tracks
    tracks_to_save = tracks[:20]
    
    # If we have fewer than 20 tracks, pad with placeholders
    while len(tracks_to_save) < 20:
        tracks_to_save.append({
            "name": f"[Track placeholder {len(tracks_to_save) + 1}]",
            "artists": [{"name": "Unknown Artist"}],
            "id": f"placeholder_{len(tracks_to_save)}",
            "external_urls": {"spotify": "#"},
            "is_placeholder": True
        })
    
    # Create the playlist entry
    playlist_entry = {
        "id": playlist_id,
        "name": playlist_name,
        "emotion": emotion,
        "tracks": tracks_to_save,
        "timestamp": timestamp,
        "input_text": input_text,
        "source": source
    }
    
    # Add to history
    st.session_state.playlist_history.append(playlist_entry)
    
    return playlist_entry

# Function to get weather-based emotion
def local_get_weather_emotion(location):
    """Get weather data and emotion from local code when agent is unavailable"""
    from weather_utils import get_weather_data, map_weather_to_emotion
    
    try:
        # Get weather data
        weather_data = get_weather_data(location)
        
        if weather_data:
            # Map weather conditions to emotion
            weather_emotion = map_weather_to_emotion(weather_data["conditions"])
            
            return {
                "status": "success",
                "weather": weather_data,
                "weather_emotion": weather_emotion
            }
        
        return {
            "status": "error",
            "error": "Could not retrieve weather data",
            "weather_emotion": "neutral"
        }
    
    except Exception as e:
        print(f"Error getting weather: {e}")
        return {
            "status": "error",
            "error": str(e),
            "weather": {"location": location, "temperature": 20, "conditions": "unknown"},
            "weather_emotion": "neutral"
        }

# Function to get weather info and associated emotion
def smart_get_weather_emotion(location):
    """Try to get weather data via agent first, then fall back to local implementation"""
    try:
        print(f"Attempting to get weather data for {location} via agent")
        response = agent_get_weather_emotion(location)
        
        if response and response.get('status') == 'success':
            print(f"Agent provided weather data")
            return response
        
        print("Using fallback weather data retrieval")
    except Exception as e:
        print(f"Error using agent system for weather: {e}")
        print("Using fallback weather data retrieval")
    
    # Fall back to local implementation
    return local_get_weather_emotion(location)

# Function to get recommendations from agent or directly
def smart_get_recommendations(emotion, limit=20):
    """Try to get recommendations via agent first, then fall back to direct API call"""
    try:
        print(f"Attempting to get recommendations for {emotion} via agent")
        response = agent_get_recommendations(emotion, limit)
        
        if response and response.get('status') == 'success' and 'tracks' in response:
            print(f"Agent provided recommendations")
            return response
        
        print("Using fallback recommendations")
    except Exception as e:
        print(f"Error using agent system for recommendations: {e}")
        print("Using fallback recommendations")
    
    # Fall back to direct API call
    try:
        tracks = search_tracks_by_mood(emotion, limit)
        return {"status": "success", "tracks": tracks}
    except Exception as e:
        print(f"Error getting direct recommendations: {e}")
        return {"status": "error", "tracks": []}

# Function to display a selected playlist
def display_playlist(playlist_arg, emotion=None):
    """
    Display details of a selected playlist.
    
    Args:
        playlist_arg: Either an index to the playlist in history or the playlist object directly
        emotion (str, optional): Emotion for styling, if not included in the playlist
    """
    # Determine if we were given an index or the playlist directly
    if isinstance(playlist_arg, int):
        # It's an index, get the playlist from history
        if playlist_arg >= len(st.session_state.playlist_history):
            st.error("Invalid playlist index")
            return
        playlist = st.session_state.playlist_history[playlist_arg]
    else:
        # It's the playlist object directly
        playlist = playlist_arg
    
    # Get the emotion for styling
    if not emotion:
        emotion = playlist.get("emotion", "neutral")
    
    # Get colors and emoji for this emotion
    color = EMOTION_STYLES[emotion]["color"]
    emoji = EMOTION_STYLES[emotion]["emoji"]
    
    # Display playlist header with styling
    st.markdown(f"<h2 style='color: {color};'>{emoji} {playlist['name']}</h2>", unsafe_allow_html=True)
    
    # Display input and emotion info
    st.markdown(f"**Original input:** \"{playlist['input_text']}\"")
    st.markdown(f"**Detected emotion:** {emoji} {emotion}")
    st.markdown(f"**Created:** {playlist['timestamp']}")
    
    # Display tracks
    st.markdown("### Tracks:")
    
    # Create a table for better display
    track_data = []
    for i, track in enumerate(playlist["tracks"], 1):
        if track.get("is_placeholder", False):
            artist = track.get("artists", [{"name": "Unknown Artist"}])[0].get("name", "Unknown")
            track_data.append({
                "#": i,
                "Title": track["name"],
                "Artist": artist,
                "Link": "#"  # Placeholder tracks don't have real links
            })
        else:
            # Handle different track formats
            if "artists" in track:
                # It's the full Spotify track format
                artist_names = ", ".join([artist["name"] for artist in track["artists"]])
                track_data.append({
                    "#": i,
                    "Title": track["name"],
                    "Artist": artist_names,
                    "Link": track.get("external_urls", {}).get("spotify", "#")
                })
            else:
                # It's a simpler format
                track_data.append({
                    "#": i,
                    "Title": track["name"],
                    "Artist": track.get("artist", "Unknown Artist"),
                    "Link": track.get("external_url", "#")
                })
    
    # Create a DataFrame for better display
    import pandas as pd
    df = pd.DataFrame(track_data)
    st.dataframe(df, hide_index=True, column_config={
        "#": st.column_config.NumberColumn(width="small"),
        "Link": st.column_config.LinkColumn("Open in Spotify")
    })
    
    # Add option to create playlist on Spotify
    if st.button("Create this playlist on Spotify", key=f"create_{playlist.get('id', 'playlist')}"):
        st.write("This would create the playlist on Spotify (functionality not implemented)")
    
    st.markdown("---")

# Function to get weather icon based on condition
def get_weather_icon(condition):
    """Helper function to get weather icon based on condition"""
    weather_icons = {
        "sunny": "☀️",
        "clear": "☀️",
        "rainy": "🌧️",
        "rain": "🌧️",
        "cloudy": "☁️",
        "clouds": "☁️",
        "snowy": "❄️",
        "snow": "❄️",
        "stormy": "⛈️",
        "thunderstorm": "⛈️",
        "foggy": "🌫️",
        "fog": "🌫️",
        "mist": "🌫️",
        "windy": "💨",
        "wind": "💨",
        "haze": "🌫️",
        "dust": "🌫️",
        "smoke": "🌫️",
        "drizzle": "🌦️",
        "tornado": "🌪️",
        "unknown": "🌈"
    }
    if not condition:
        return "🌈"
    
    condition = condition.lower()
    return weather_icons.get(condition, "🌈")

# Function to get a stylized emoji for a given emotion
def get_emotion_emoji(emotion):
    """Get the emoji associated with a specific emotion."""
    if emotion in EMOTION_STYLES:
        return EMOTION_STYLES[emotion]["emoji"]
    return "😐"

# Main application
def main():
    """Main application function to render the Streamlit UI"""
    # Add sidebar with Spotify logo and settings
    with st.sidebar:
        st.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png", width=200)
        st.markdown("## Settings & Info")
        
        # API Status Section
        st.markdown("### 🔌 API Status")
        st.info("✅ Spotify API: Connected")
        st.info("🔄 Agent System: Fallback Mode")
        
        # Current emotion indicator
        current_emotion = st.session_state.current_emotion
        emoji = EMOTION_STYLES[current_emotion]["emoji"]
        st.markdown(f"### Current Mood: {emoji} {current_emotion.title()}")
        
        # Troubleshooting expandable section
        with st.expander("⚙️ Troubleshooting"):
            st.write("### Common Issues")
            st.write("- OpenAI API limit exceeded (using fallback)")
            st.write("- Agent communication issues (using direct API)")
    
    # Display the header with a mood-appropriate styling and Spotify logo
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"<h1 style='color: #1DB954;'>🎵 Mood & Weather Playlist Creator</h1>", unsafe_allow_html=True)
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Spotify_icon.svg/1982px-Spotify_icon.svg.png", width=60)
    
    st.markdown("<p style='font-size: 1.2em;'>Create personalized playlists based on your mood or local weather</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Create tabs with icons
    tab1, tab2, tab3 = st.tabs(["🎭 Create Mood Playlist", "📚 Your Playlist History", "🌦️ Weather Playlist"])
    
    # Tab 1: Create a new playlist based on text input
    with tab1:
        st.subheader("✨ Create a Mood-Based Playlist")
        
        # Text input for mood detection
        user_input = st.text_area("Describe your mood or the vibe you want:", 
                                  height=100,
                                  placeholder="Example: I'm feeling nostalgic about my childhood summers...")
        
        # Generate button with the current emotion style
        emotion = st.session_state.current_emotion
        color = EMOTION_STYLES[emotion]["color"]
        if st.button(f"✨ Generate Playlist", key="generate_btn", type="primary"):
            if user_input:
                # Display a spinner while processing
                with st.spinner("Creating your personalized playlist..."):
                    # Get the emotion from the user input
                    emotion = smart_detect_emotion(user_input)
                    st.session_state.current_emotion = emotion
                    
                    # Display the detected emotion with styling
                    color = EMOTION_STYLES[emotion]["color"]
                    emoji = EMOTION_STYLES[emotion]["emoji"]
                    st.markdown(f"<div style='padding: 15px; border-radius: 8px; background-color: {color}20;'>"
                                f"<h3>{emoji} Your mood: {emotion.title()}</h3>"
                                f"</div>", unsafe_allow_html=True)
                    
                    # Get music recommendations based on emotion
                    recommendations = smart_get_recommendations(emotion, limit=20)
                    
                    # Extract tracks from the response dictionary
                    if recommendations and 'status' in recommendations and recommendations['status'] == 'success':
                        tracks = recommendations.get('tracks', [])
                    else:
                        tracks = []
                    
                    if tracks:
                        # Save to history
                        playlist = save_playlist_to_history(user_input, emotion, tracks)
                        
                        # Display the playlist
                        st.subheader(f"{emoji} Your Customized Playlist:")
                        
                        # Display the playlist
                        display_playlist(playlist)
                    else:
                        st.error("Could not generate recommendations. Please try again.")
            else:
                st.error("Please enter some text to analyze")
    
    # Tab 2: View previous playlists
    with tab2:
        st.subheader("📚 Your Previous Playlists")
        
        if not st.session_state.playlist_history:
            st.info("👋 You haven't created any playlists yet. Create one from the first tab!")
        else:
            # Display a summary of saved playlists
            st.markdown(f"<p style='font-size: 1.2em;'>You have created {len(st.session_state.playlist_history)} playlists so far.</p>", unsafe_allow_html=True)
            
            # Create a grid of buttons for the playlists
            cols = st.columns(3)
            
            for i, playlist in enumerate(st.session_state.playlist_history):
                col_idx = i % 3
                emotion = playlist["emotion"]
                color = EMOTION_STYLES[emotion]["color"]
                emoji = EMOTION_STYLES[emotion]["emoji"]
                
                with cols[col_idx]:
                    button_label = f"{emoji} {playlist['name']}"
                    if st.button(button_label, key=f"history_{i}"):
                        # Display the selected playlist
                        display_playlist(i, emotion)
            
            # Option to clear history
            st.markdown("---")
            if st.button("🗑️ Clear All Playlist History", key="clear_history"):
                st.session_state.playlist_history = []
                st.experimental_rerun()
    
    # Tab 3: Weather-based playlist
    with tab3:
        st.subheader("🌦️ Create a Weather-Based Playlist")
        st.write("Let the weather decide your musical mood! Enter your city to get a playlist that matches the current weather.")
        
        # City input
        city = st.text_input("🌍 Enter your city:", placeholder="e.g. New York, Tokyo, London")
        
        if st.button("🌦️ Get Weather Playlist", key="weather_btn", type="primary"):
            if city:
                # Display a spinner while processing
                with st.spinner("Creating a weather-inspired playlist..."):
                    # Get weather-based emotion
                    weather_data = smart_get_weather_emotion(city)
                    emotion = weather_data["weather_emotion"]
                    st.session_state.current_emotion = emotion
                    
                    # Weather display
                    weather_icon = get_weather_icon(weather_data["weather"]["conditions"])
                    emoji = EMOTION_STYLES[emotion]["emoji"]
                    color = EMOTION_STYLES[emotion]["color"]
                    
                    st.markdown(f"<div style='padding: 15px; border-radius: 8px; background-color: {color}20;'>"
                               f"<h3>{weather_icon} Weather in {city}</h3>"
                               f"<p>Condition: <b>{weather_data['weather']['conditions']}</b></p>"
                               f"<p>Temperature: <b>{weather_data['weather']['temperature']}°C</b></p>"
                               f"<p>Suggested mood: <b>{emoji} {emotion}</b></p>"
                               f"</div>", unsafe_allow_html=True)
                    
                    # Get music recommendations based on weather-generated emotion
                    recommendations = smart_get_recommendations(emotion, limit=20)
                    
                    # Extract tracks from the response dictionary
                    if recommendations and 'status' in recommendations and recommendations['status'] == 'success':
                        tracks = recommendations.get('tracks', [])
                    else:
                        tracks = []
                    
                    if tracks:
                        # Save to history with weather source
                        playlist_name = f"Weather: {city} ({emotion.capitalize()})"
                        playlist = save_playlist_to_history(
                           f"{city} - {weather_data['weather']['conditions']}", 
                            emotion, 
                            tracks, 
                            source="weather"
                        )
                        
                        # Display the playlist
                        st.subheader(f"{weather_icon} Your Weather-Inspired Playlist:")
                        
                        # Display the playlist
                        display_playlist(playlist)
                    else:
                        # Display mock tracks if we couldn't get recommendations
                        st.warning("Could not get music recommendations. Showing mock tracks instead.")
                        
                        # Create mock tracks
                        mock_tracks = []
                        for i in range(20):
                            mock_tracks.append({
                                "name": f"Weather Song {i+1}",
                                "artists": [{"name": f"Weather Artist {(i % 5) + 1}"}],
                                "id": f"mock_{i}",
                                "external_urls": {"spotify": "#"},
                                "album": f"The {weather_data['weather']['conditions'].title()} Album",
                                "image_url": None,
                                "preview_url": None,
                            })
                        
                        # Save to history
                        playlist = save_playlist_to_history(
                           f"{city} - {weather_data['weather']['conditions']}", 
                            emotion, 
                            mock_tracks, 
                            source="weather"
                        )
                        
                        # Display the playlist
                        st.subheader(f"{weather_icon} Your Weather-Inspired Playlist (Mock Data):")
                        
                        # Display the playlist
                        display_playlist(playlist)
            else:
                st.error("Please enter a city name")
    
    # Add informational footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #888;">
        <p>This app creates personalized playlists based on your mood or local weather.</p>
        <p>Made with ❤️ using Streamlit, Spotify, and OpenAI.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Run the main application
if __name__ == "__main__":
    main() 
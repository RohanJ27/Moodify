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
    "energetic": {"color": "#FF7F50", "emoji": "⚡", "gradient": ["#FF7F50", "#FF4500"]}
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

# Define simple emotion detection function
def detect_emotion(text):
    """Simple function to detect emotion in text"""
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
                return emotion
    
    # Default to random emotion if nothing detected
    return random.choice(list(emotions.keys()))

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
    tracks = tracks[:20]
    
    # Create the playlist entry
    playlist_entry = {
        "id": playlist_id,
        "name": playlist_name,
        "input_text": input_text,
        "emotion": emotion,
        "tracks": tracks,
        "timestamp": timestamp,
        "source": source
    }
    
    # Add to session state
    st.session_state.playlist_history.append(playlist_entry)
    
    return playlist_entry

# Get weather data and emotion
def get_weather_emotion(location):
    """Simple function to get weather data and associated emotion"""
    # In a real implementation, this would call a weather API
    weather_conditions = ["sunny", "rainy", "cloudy", "snowy", "stormy", "foggy", "windy"]
    emotions = ["happy", "sad", "calm", "relaxed", "excited", "melancholy", "energetic"]
    
    condition = random.choice(weather_conditions)
    emotion = emotions[weather_conditions.index(condition)]
    
    # Weather condition icons
    weather_icons = {
        "sunny": "☀️",
        "rainy": "🌧️",
        "cloudy": "☁️",
        "snowy": "❄️",
        "stormy": "⛈️",
        "foggy": "🌫️",
        "windy": "💨"
    }
    
    return {
        "weather_condition": condition,
        "temperature": random.randint(0, 30),
        "emotion": emotion,
        "icon": weather_icons.get(condition, "🌈")
    }

# Display a single playlist from history
def display_playlist(playlist):
    """
    Display a single playlist from history with mood-based styling.
    
    Args:
        playlist (dict): Playlist data including tracks, emotion, etc.
    """
    emotion = playlist["emotion"]
    color = EMOTION_STYLES[emotion]["color"]
    emoji = EMOTION_STYLES[emotion]["emoji"]
    
    # Create a container with a border style matching the emotion
    with st.container():
        st.markdown(f"<h2 style='color:{color};'>{playlist['name']}</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Created:** {playlist['timestamp']}")
            st.markdown(f"**Emotion:** {emoji} {playlist['emotion'].title()}")
        
            # Show original input
            st.markdown("**Original input:**")
            st.info(playlist["input_text"])
        
        with col2:
            # Add a create playlist button
            if st.button(f"🎵 Create on Spotify", key=f"create_{playlist['id']}"):
                # Get the current user
                user = get_current_user()
                if not user:
                    st.error("Please connect to Spotify first")
                    st.info("Note: Creating playlists requires user authentication, which may not be set up in this demo.")
                else:
                    # Create playlist directly
                    spotify_playlist = create_playlist(
                        user_id=user["id"],
                        playlist_name=playlist["name"],
                        track_ids=[track["id"] for track in playlist["tracks"] if "id" in track],
                        description=f"A playlist based on the emotion: {playlist['emotion']}"
                    )
                    
                    if spotify_playlist:
                        st.success(f"Playlist created! [Open in Spotify]({spotify_playlist['url']})")
                    else:
                        st.error("Failed to create playlist on Spotify")
        
        # Display tracks in a more appealing grid layout
        st.markdown(f"<h3 style='color:{color};'>Tracks ({len(playlist['tracks'])}):</h3>", unsafe_allow_html=True)
        
        # Create rows of 2 tracks each for better visual layout
        tracks = playlist['tracks']
        for i in range(0, len(tracks), 2):
            col1, col2 = st.columns(2)
            
            # First track in the row
            with col1:
                if i < len(tracks):
                    track = tracks[i]
                    with st.container():
                        st.markdown(f"**{i+1}. {track['name']}**")
                        st.markdown(f"by {track['artist']}")
                        if track.get('image_url'):
                            st.image(track['image_url'], width=100)
                        if track.get('external_url'):
                            st.markdown(f"[Open in Spotify]({track['external_url']})")
            
            # Second track in the row (if available)
            with col2:
                if i+1 < len(tracks):
                    track = tracks[i+1]
                    with st.container():
                        st.markdown(f"**{i+2}. {track['name']}**")
                        st.markdown(f"by {track['artist']}")
                        if track.get('image_url'):
                            st.image(track['image_url'], width=100)
                        if track.get('external_url'):
                            st.markdown(f"[Open in Spotify]({track['external_url']})")

# Main application
def main():
    # Get current emotion for styling
    current_emotion = st.session_state.get('current_emotion', 'neutral')
    
    # Sidebar with app info and settings
    with st.sidebar:
        st.image("https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_Green.png", width=200)
        st.markdown("## Settings & Info")
        
        # API Status Section
        st.markdown("### 🔌 API Connection")
        
        if st.button("Check API Connection", key="check_api"):
            with st.spinner("Testing Spotify API connection..."):
                health_check = spotify_api_health_check()
                
                if health_check["success"]:
                    st.success("✅ Spotify API is working correctly")
                else:
                    st.error("❌ Spotify API connection issues detected")
                
                st.subheader("Details:")
                for message in health_check["messages"]:
                    st.write(f"- {message}")
                
                # Display environment variable status
                st.subheader("Environment Variables:")
                if health_check["env_vars_set"]:
                    st.write("✅ Environment variables are set correctly")
                else:
                    st.write("❌ Missing required environment variables")
                    st.info("Make sure SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are set in your .env file")
        
        # Troubleshooting expandable section
        with st.expander("⚙️ Troubleshooting"):
            st.write("### Spotify API Troubleshooting")
            st.write("If you're experiencing issues with the Spotify integration, try these steps:")
            
            st.write("1. **Check your Spotify credentials**")
            st.write("   Make sure your `.env` file contains valid Spotify API credentials:")
            st.code("""
            SPOTIFY_CLIENT_ID=your_client_id_here
            SPOTIFY_CLIENT_SECRET=your_client_secret_here
            SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
            """)
            
            st.write("2. **Test your API connection**")
            st.write("   Use the 'Check API Connection' button above to verify your credentials are working.")
            
            st.write("3. **Common issues:**")
            st.write("   - Invalid client ID or secret")
            st.write("   - API rate limiting (try again later)")
            st.write("   - Network connectivity problems")
            st.write("   - Spotify API service outages")
            
            if st.button("Run Manual Authentication Test", key="run_manual_test"):
                with st.spinner("Testing authentication..."):
                    result = test_spotify_authentication()
                    if result:
                        st.success("Authentication test passed successfully!")
                    else:
                        st.error("Authentication test failed. Check the console for detailed logs.")
    
    # Main content area
    # App title
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"<h1 style='color: #1DB954;'>🎵 Mood & Weather Playlist Creator</h1>", unsafe_allow_html=True)
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Spotify_icon.svg/1982px-Spotify_icon.svg.png", width=60)
    
    st.markdown("<p style='font-size: 1.2em;'>Create personalized playlists based on your mood or local weather</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Create tabs with icons
    tab1, tab2, tab3 = st.tabs(["🎭 Create Mood Playlist", "📚 Your Playlist History", "🌦️ Weather Playlist"])
    
    # Tab 1: Create Playlist
    with tab1:
        styled_header("Create a Mood-Based Playlist", current_emotion)
        
        # Input container with styling
        with st.container():
            st.write("Tell us how you're feeling, and we'll create the perfect playlist for you!")
            
            # Get user input with a larger, more appealing text area
            user_input = st.text_area(
                "Describe your mood or the vibe you want for your playlist:",
                height=100,
                placeholder="Example: I'm feeling really energetic and ready to take on the day!"
            )
            
            # Process button with custom styling
            generate_col1, generate_col2 = st.columns([1, 3])
            with generate_col1:
                generate_button = st.button("✨ Generate Playlist", key="generate_playlist_button")
            
            if generate_button:
                if user_input:
                    with st.spinner("Creating your personalized playlist..."):
                        # Get the emotion from the user input
                        emotion = detect_emotion(user_input)
                        st.session_state.current_emotion = emotion
                        
                        # Show detected emotion with icon and color
                        emoji = EMOTION_STYLES[emotion]["emoji"]
                        color = EMOTION_STYLES[emotion]["color"]
                        
                        st.markdown(f"<div style='padding: 10px; border-radius: 5px; background-color: {color}20;'>"
                                   f"<h3>Detected Mood: {emoji} {emotion.title()}</h3>"
                                   f"</div>", unsafe_allow_html=True)
                        
                        # Get music recommendations based on emotion - now with exactly 20 tracks
                        tracks = search_tracks_by_mood(emotion, limit=20)
                        
                        if tracks:
                            # Save to history
                            playlist = save_playlist_to_history(user_input, emotion, tracks)
                            
                            # Create a container for the playlist
                            with st.container():
                                st.markdown(f"<h2 style='color: {color};'>{emoji} Your New Playlist</h2>", unsafe_allow_html=True)
                                
                                # Display tracks in a grid layout (10 visible, 10 in expander)
                                st.write("Check out your personalized tracks:")
                                
                                # Create columns for better visual layout
                                for i in range(0, 10, 2):
                                    col1, col2 = st.columns(2)
                                    
                                    # First track in the row
                                    with col1:
                                        if i < len(tracks):
                                            track = tracks[i]
                                            with st.container():
                                                st.markdown(f"**{i+1}. {track['name']}**")
                                                st.markdown(f"by {track['artist']}")
                                                if track.get('image_url'):
                                                    st.image(track['image_url'], width=100)
                                                if track.get('external_url'):
                                                    st.markdown(f"[Open in Spotify]({track['external_url']})")
                                    
                                    # Second track in the row
                                    with col2:
                                        if i+1 < len(tracks):
                                            track = tracks[i+1]
                                            with st.container():
                                                st.markdown(f"**{i+2}. {track['name']}**")
                                                st.markdown(f"by {track['artist']}")
                                                if track.get('image_url'):
                                                    st.image(track['image_url'], width=100)
                                                if track.get('external_url'):
                                                    st.markdown(f"[Open in Spotify]({track['external_url']})")
                                
                                # Create an expander for the remaining tracks
                                with st.expander("🔽 Show More Tracks"):
                                    for i in range(10, 20, 2):
                                        col1, col2 = st.columns(2)
                                        
                                        # First track in the row
                                        with col1:
                                            if i < len(tracks):
                                                track = tracks[i]
                                                with st.container():
                                                    st.markdown(f"**{i+1}. {track['name']}**")
                                                    st.markdown(f"by {track['artist']}")
                                                    if track.get('image_url'):
                                                        st.image(track['image_url'], width=100)
                                                    if track.get('external_url'):
                                                        st.markdown(f"[Open in Spotify]({track['external_url']})")
                                        
                                        # Second track in the row
                                        with col2:
                                            if i+1 < len(tracks):
                                                track = tracks[i+1]
                                                with st.container():
                                                    st.markdown(f"**{i+2}. {track['name']}**")
                                                    st.markdown(f"by {track['artist']}")
                                                    if track.get('image_url'):
                                                        st.image(track['image_url'], width=100)
                                                    if track.get('external_url'):
                                                        st.markdown(f"[Open in Spotify]({track['external_url']})")
                                
                                # Create playlist button
                                st.button(f"🎵 Create Playlist on Spotify", key="create_spotify_playlist", type="primary")
                        else:
                            st.warning("⚠️ No recommendations received from Spotify API")
                            st.info("ℹ️ Using mock recommendations instead")
                            
                            # Create some mock recommendations - ensure exactly 20 tracks
                            mock_emotions = {
                                "happy": ["Joyful", "Cheerful", "Upbeat", "Sunny", "Delightful"],
                                "sad": ["Melancholy", "Tearful", "Heartbreak", "Blue", "Somber"],
                                "angry": ["Rage", "Fury", "Intense", "Fierce", "Aggressive"],
                                "relaxed": ["Peaceful", "Serene", "Calm", "Tranquil", "Mellow"],
                                "anxious": ["Tense", "Worried", "Uneasy", "Restless", "Nervous"],
                                "neutral": ["Balanced", "Steady", "Regular", "Plain", "Moderate"],
                                "nostalgic": ["Memory", "Remember", "Childhood", "Past", "Golden"],
                                "energetic": ["Dynamic", "Vibrant", "Active", "Energy", "Power"]
                            }
                            
                            artists = ["Mood Artist", "Emotion Band", "Feeling Collective", "Vibe Creators", 
                                     "Sonic Mood", "Harmony Group", "Rhythm Masters", "Melody Makers",
                                     "The Expressions", "Ambient Sounds", "Tone Setters", "Sound Painters"]
                            
                            # Create 20 unique mock tracks
                            mock_tracks = []
                            adjectives = mock_emotions.get(emotion, mock_emotions["neutral"])
                            
                            for i in range(20):
                                adj = random.choice(adjectives)
                                artist = random.choice(artists)
                                mock_tracks.append({
                                    "id": f"mock_{i}",
                                    "name": f"{adj} {['Song', 'Tune', 'Melody', 'Rhythm', 'Beat'][i % 5]} {i+1}",
                                    "artist": artist,
                                    "album": f"The {emotion.title()} Album",
                                    "image_url": None,
                                    "preview_url": None,
                                    "external_url": "https://spotify.com"
                                })
                            
                            # Save to history
                            playlist = save_playlist_to_history(user_input, emotion, mock_tracks)
                            
                            # Display mock tracks with emotion-based styling
                            emoji = EMOTION_STYLES[emotion]["emoji"]
                            color = EMOTION_STYLES[emotion]["color"]
                            
                            st.markdown(f"<h3 style='color: {color};'>{emoji} Mock Recommendations</h3>", unsafe_allow_html=True)
                            
                            # Display tracks in a grid layout
                            for i in range(0, 10, 2):
                                col1, col2 = st.columns(2)
                                
                                # First track
                                with col1:
                                    if i < len(mock_tracks):
                                        track = mock_tracks[i]
                                        st.markdown(f"**{i+1}. {track['name']}**")
                                        st.markdown(f"by {track['artist']}")
                                
                                # Second track
                                with col2:
                                    if i+1 < len(mock_tracks):
                                        track = mock_tracks[i+1]
                                        st.markdown(f"**{i+2}. {track['name']}**")
                                        st.markdown(f"by {track['artist']}")
                            
                            # Create an expander for the remaining tracks
                            with st.expander("🔽 Show More Tracks"):
                                for i in range(10, 20, 2):
                                    col1, col2 = st.columns(2)
                                    
                                    # First track
                                    with col1:
                                        if i < len(mock_tracks):
                                            track = mock_tracks[i]
                                            st.markdown(f"**{i+1}. {track['name']}**")
                                            st.markdown(f"by {track['artist']}")
                                    
                                    # Second track
                                    with col2:
                                        if i+1 < len(mock_tracks):
                                            track = mock_tracks[i+1]
                                            st.markdown(f"**{i+2}. {track['name']}**")
                                            st.markdown(f"by {track['artist']}")
                else:
                    st.warning("⚠️ Please enter some text describing your emotion or desired playlist mood")

    # Tab 2: Previous Playlists
    with tab2:
        styled_header("Your Playlist History", current_emotion)
        
        # Check if we have any playlist history
        if not st.session_state.playlist_history:
            st.info("👋 You haven't created any playlists yet. Go to the 'Create Mood Playlist' tab to get started!")
        else:
            # Display a summary of saved playlists
            st.markdown(f"<p style='font-size: 1.2em;'>You have created {len(st.session_state.playlist_history)} playlists so far.</p>", unsafe_allow_html=True)
            
            # Create a selection list for all playlists with better styling
            playlist_options = [f"{playlist['name']} - {playlist['timestamp']}" 
                              for playlist in st.session_state.playlist_history]
            
            selected_playlist = st.selectbox(
                "Select a playlist to view:",
                options=playlist_options,
                index=0
            )
            
            # Find the selected playlist
            if selected_playlist:
                # Find the index of the selected playlist
                selected_timestamp = selected_playlist.split(" - ")[-1]
                selected_playlist_obj = None
                
                for playlist in st.session_state.playlist_history:
                    if playlist["timestamp"] == selected_timestamp:
                        selected_playlist_obj = playlist
                        break
                
                if selected_playlist_obj:
                    # Display the selected playlist with styling
                    display_playlist(selected_playlist_obj)
            
            # Option to clear history
            st.markdown("---")
            if st.button("🗑️ Clear All Playlist History", key="clear_history"):
                st.session_state.playlist_history = []
                st.experimental_rerun()

    # Tab 3: Weather Playlist
    with tab3:
        styled_header("Weather-Based Playlist", current_emotion)
        
        st.markdown("<p style='font-size: 1.2em;'>Let the weather decide your musical mood! Enter your city to get a playlist that matches the current weather conditions.</p>", unsafe_allow_html=True)
        
        # Create a weather input area
        with st.container():
            city = st.text_input("🌍 Enter city name:", placeholder="e.g. New York, Tokyo, London")
            
            weather_col1, weather_col2 = st.columns([1, 3])
            with weather_col1:
                if st.button("🌦️ Get Weather Playlist", key="get_weather"):
                    if city:
                        with st.spinner("Fetching weather and creating your playlist..."):
                            # Get weather-based emotion
                            weather_data = get_weather_emotion(city)
                            emotion = weather_data["emotion"]
                            st.session_state.current_emotion = emotion
                            
                            # Weather display
                            weather_icon = weather_data["icon"]
                            emoji = EMOTION_STYLES[emotion]["emoji"]
                            color = EMOTION_STYLES[emotion]["color"]
                            
                            st.markdown(f"<div style='padding: 15px; border-radius: 8px; background-color: {color}20;'>"
                                       f"<h3>{weather_icon} Weather in {city}</h3>"
                                       f"<p>Condition: <b>{weather_data['weather_condition']}</b></p>"
                                       f"<p>Temperature: <b>{weather_data['temperature']}°C</b></p>"
                                       f"<p>Suggested mood: <b>{emoji} {emotion}</b></p>"
                                       f"</div>", unsafe_allow_html=True)
                            
                            # Get music recommendations based on weather-generated emotion - exactly 20 tracks
                            tracks = search_tracks_by_mood(emotion, limit=20)
                            
                            if tracks:
                                # Save to history with weather source
                                playlist = save_playlist_to_history(
                                    f"{city} - {weather_data['weather_condition']}", 
                                    emotion, 
                                    tracks, 
                                    source="weather"
                                )
                                
                                # Display the weather playlist
                                st.markdown(f"<h2 style='color: {color};'>{weather_icon} Your Weather Playlist</h2>", unsafe_allow_html=True)
                                
                                # Display tracks in a grid layout
                                for i in range(0, 10, 2):
                                    col1, col2 = st.columns(2)
                                    
                                    # First track
                                    with col1:
                                        if i < len(tracks):
                                            track = tracks[i]
                                            with st.container():
                                                st.markdown(f"**{i+1}. {track['name']}**")
                                                st.markdown(f"by {track['artist']}")
                                                if track.get('image_url'):
                                                    st.image(track['image_url'], width=100)
                                                if track.get('external_url'):
                                                    st.markdown(f"[Open in Spotify]({track['external_url']})")
                                    
                                    # Second track
                                    with col2:
                                        if i+1 < len(tracks):
                                            track = tracks[i+1]
                                            with st.container():
                                                st.markdown(f"**{i+2}. {track['name']}**")
                                                st.markdown(f"by {track['artist']}")
                                                if track.get('image_url'):
                                                    st.image(track['image_url'], width=100)
                                                if track.get('external_url'):
                                                    st.markdown(f"[Open in Spotify]({track['external_url']})")
                                
                                # Create an expander for the remaining tracks
                                with st.expander("🔽 Show More Tracks"):
                                    for i in range(10, len(tracks), 2):
                                        col1, col2 = st.columns(2)
                                        
                                        # First track
                                        with col1:
                                            if i < len(tracks):
                                                track = tracks[i]
                                                with st.container():
                                                    st.markdown(f"**{i+1}. {track['name']}**")
                                                    st.markdown(f"by {track['artist']}")
                                                    if track.get('image_url'):
                                                        st.image(track['image_url'], width=100)
                                                    if track.get('external_url'):
                                                        st.markdown(f"[Open in Spotify]({track['external_url']})")
                                        
                                        # Second track
                                        with col2:
                                            if i+1 < len(tracks):
                                                track = tracks[i+1]
                                                with st.container():
                                                    st.markdown(f"**{i+2}. {track['name']}**")
                                                    st.markdown(f"by {track['artist']}")
                                                    if track.get('image_url'):
                                                        st.image(track['image_url'], width=100)
                                                    if track.get('external_url'):
                                                        st.markdown(f"[Open in Spotify]({track['external_url']})")
                                
                                # Create playlist option
                                st.button(f"🎵 Create Weather Playlist on Spotify", key="create_weather_playlist", type="primary")
                            else:
                                st.warning("⚠️ No recommendations received from Spotify API")
                                st.info("ℹ️ Using mock recommendations instead")
                                
                                # Create some mock recommendations - ensure exactly 20 tracks
                                mock_tracks = []
                                for i in range(20):
                                    mock_tracks.append({
                                        "id": f"mock_weather_{i}",
                                        "name": f"Weather Song {i+1}",
                                        "artist": f"Weather Artist {(i % 5) + 1}",
                                        "album": f"The {weather_data['weather_condition'].title()} Album",
                                        "image_url": None,
                                        "preview_url": None,
                                        "external_url": "https://spotify.com"
                                    })
                                
                                # Save to history
                                playlist = save_playlist_to_history(
                                    f"{city} - {weather_data['weather_condition']}", 
                                    emotion, 
                                    mock_tracks, 
                                    source="weather"
                                )
                                
                                # Display mock tracks with emotion-based styling
                                st.markdown(f"<h3 style='color: {color};'>{weather_icon} Weather Playlist (Mock)</h3>", unsafe_allow_html=True)
                                
                                # Display tracks in a grid layout
                                for i in range(0, 10, 2):
                                    col1, col2 = st.columns(2)
                                    
                                    # First track
                                    with col1:
                                        if i < len(mock_tracks):
                                            track = mock_tracks[i]
                                            st.markdown(f"**{i+1}. {track['name']}**")
                                            st.markdown(f"by {track['artist']}")
                                    
                                    # Second track
                                    with col2:
                                        if i+1 < len(mock_tracks):
                                            track = mock_tracks[i+1]
                                            st.markdown(f"**{i+2}. {track['name']}**")
                                            st.markdown(f"by {track['artist']}")
                                
                                # Create an expander for the remaining tracks
                                with st.expander("🔽 Show More Tracks"):
                                    for i in range(10, 20, 2):
                                        col1, col2 = st.columns(2)
                                        
                                        # First track
                                        with col1:
                                            if i < len(mock_tracks):
                                                track = mock_tracks[i]
                                                st.markdown(f"**{i+1}. {track['name']}**")
                                                st.markdown(f"by {track['artist']}")
                                        
                                        # Second track
                                        with col2:
                                            if i+1 < len(mock_tracks):
                                                track = mock_tracks[i+1]
                                                st.markdown(f"**{i+2}. {track['name']}**")
                                                st.markdown(f"by {track['artist']}")
                    else:
                        st.warning("⚠️ Please enter a city name")

    # Footer
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #888888;'>© 2023 Mood & Weather Playlist Creator | Powered by Spotify</div>", unsafe_allow_html=True)

# Run the main application
if __name__ == "__main__":
    main() 
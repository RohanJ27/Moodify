import os
import sys
import asyncio
import nest_asyncio
import uuid
import streamlit as st
import random
import datetime

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

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Initialize playlist history
if 'playlist_history' not in st.session_state:
    st.session_state.playlist_history = []

# Define simple emotion detection function
def detect_emotion(text):
    """Simple function to detect emotion in text"""
    emotions = {
        "happy": ["happy", "joy", "joyful", "excited", "cheerful", "delighted", "content"],
        "sad": ["sad", "unhappy", "depressed", "down", "blue", "melancholy", "gloomy"],
        "angry": ["angry", "mad", "furious", "irritated", "annoyed", "enraged"],
        "relaxed": ["relaxed", "calm", "peaceful", "serene", "tranquil", "chilled"],
        "anxious": ["anxious", "worried", "nervous", "stressed", "tense", "uneasy"],
        "neutral": ["neutral", "ok", "okay", "fine", "alright"]
    }
    
    text = text.lower()
    
    for emotion, keywords in emotions.items():
        for keyword in keywords:
            if keyword in text:
                return emotion
    
    # Default to random emotion if nothing detected
    return random.choice(list(emotions.keys()))

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
        playlist_name = f"Weather: {input_text} ({emotion.title()})"
    else:
        # Use first few words of input as the playlist name
        words = input_text.split()[:4]
        short_input = " ".join(words)
        if len(short_input) > 30:
            short_input = short_input[:27] + "..."
        playlist_name = f"{emotion.title()}: {short_input}"
    
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
    
    return {
        "weather_condition": condition,
        "temperature": random.randint(0, 30),
        "emotion": emotion
    }

# Display a single playlist from history
def display_playlist(playlist):
    """
    Display a single playlist from history.
    
    Args:
        playlist (dict): Playlist data including tracks, emotion, etc.
    """
    st.subheader(playlist["name"])
    st.write(f"**Created:** {playlist['timestamp']}")
    st.write(f"**Emotion:** {playlist['emotion']}")
    
    # Show original input
    st.write("**Original input:**")
    st.info(playlist["input_text"])
    
    # Display all tracks
    st.write(f"**Tracks ({len(playlist['tracks'])}):**")
    
    # Create columns for better display
    for i, track in enumerate(playlist['tracks'], 1):
        col1, col2 = st.columns([1, 3])
        with col1:
            if track.get('image_url'):
                st.image(track['image_url'], width=60)
            else:
                st.write(f"{i}.")
        with col2:
            st.write(f"**{track['name']}**")
            st.write(f"by {track['artist']}")
            if track.get('external_url'):
                st.write(f"[Open in Spotify]({track['external_url']})")
        
        # Add a separator line
        if i < len(playlist['tracks']):
            st.markdown("---")
    
    # Button to create this playlist on Spotify
    if st.button(f"Create '{playlist['name']}' on Spotify", key=f"create_{playlist['id']}"):
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

# Define the UI
st.title("Music Emotion Assistant")

# Add Spotify API status in sidebar
with st.sidebar:
    st.header("Spotify API Status")
    
    if st.button("Check API Connection"):
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
            
            # Display detailed test button
            if st.button("Run Detailed Test"):
                st.code(test_spotify_authentication())

# Main tabs for app navigation
tab1, tab2, tab3 = st.tabs(["Create Playlist", "Previous Playlists", "Weather Playlist"])

# Tab 1: Create Playlist
with tab1:
    st.header("Create a Mood-Based Playlist")
    
    # Get user input
    user_input = st.text_area("Tell me how you're feeling or describe the mood for your playlist:", height=100)
    
    # Process button
    if st.button("Generate Playlist"):
        if user_input:
            with st.spinner("Creating your playlist..."):
                # Get the emotion from the user input
                emotion = detect_emotion(user_input)
                
                st.write(f"Detected emotion: **{emotion}**")
                
                # Get music recommendations based on emotion - now with exactly 20 tracks
                tracks = search_tracks_by_mood(emotion, limit=20)
                
                if tracks:
                    # Save to history
                    playlist = save_playlist_to_history(user_input, emotion, tracks)
                    
                    st.write("### Your New Playlist:")
                    
                    # Display tracks
                    for i, track in enumerate(tracks[:10], 1):  # Show first 10 tracks initially
                        st.write(f"{i}. **{track['name']}** by {track['artist']}")
                        if track.get('image_url'):
                            st.image(track['image_url'], width=100)
                        if track.get('external_url'):
                            st.write(f"[Open in Spotify]({track['external_url']})")
                    
                    # Create an expander for the remaining tracks
                    with st.expander("Show more tracks"):
                        for i, track in enumerate(tracks[10:], 11):
                            st.write(f"{i}. **{track['name']}** by {track['artist']}")
                            if track.get('image_url'):
                                st.image(track['image_url'], width=100)
                            if track.get('external_url'):
                                st.write(f"[Open in Spotify]({track['external_url']})")
                    
                    # Create playlist option
                    if st.button("Create Spotify Playlist"):
                        # First get the current user
                        user = get_current_user()
                        if not user:
                            st.error("Please connect to Spotify first")
                            st.info("Note: Creating playlists requires user authentication, which may not be set up in this demo.")
                        else:
                            # Create playlist directly
                            spotify_playlist = create_playlist(
                                user_id=user["id"],
                                playlist_name=playlist["name"],
                                track_ids=[track["id"] for track in tracks if "id" in track],
                                description=f"A playlist based on the emotion: {emotion}"
                            )
                            
                            if spotify_playlist:
                                st.success(f"Playlist created! [Open in Spotify]({spotify_playlist['url']})")
                            else:
                                st.error("Failed to create playlist")
                else:
                    st.warning("No recommendations received from Spotify API")
                    st.info("Using mock recommendations instead")
                    
                    # Create some mock recommendations - ensure exactly 20 tracks
                    mock_emotions = {
                        "happy": ["Joyful", "Cheerful", "Upbeat", "Sunny", "Delightful"],
                        "sad": ["Melancholy", "Tearful", "Heartbreak", "Blue", "Somber"],
                        "angry": ["Rage", "Fury", "Intense", "Fierce", "Aggressive"],
                        "relaxed": ["Peaceful", "Serene", "Calm", "Tranquil", "Mellow"],
                        "anxious": ["Tense", "Worried", "Uneasy", "Restless", "Nervous"],
                        "neutral": ["Balanced", "Steady", "Regular", "Plain", "Moderate"]
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
                    
                    st.write("### Mock Recommendations:")
                    for i, track in enumerate(mock_tracks[:10], 1):
                        st.write(f"{i}. **{track['name']}** by {track['artist']}")
                    
                    # Create an expander for the remaining tracks
                    with st.expander("Show more tracks"):
                        for i, track in enumerate(mock_tracks[10:], 11):
                            st.write(f"{i}. **{track['name']}** by {track['artist']}")
        else:
            st.warning("Please enter some text describing your emotion or desired playlist mood")

# Tab 2: Previous Playlists
with tab2:
    st.header("Your Playlist History")
    
    # Check if we have any playlist history
    if not st.session_state.playlist_history:
        st.info("You haven't created any playlists yet. Go to the 'Create Playlist' tab to get started!")
    else:
        st.write(f"You have created {len(st.session_state.playlist_history)} playlists so far.")
        
        # Create a selection list for all playlists
        playlist_options = [f"{i+1}. {playlist['name']} - {playlist['timestamp']}" 
                          for i, playlist in enumerate(st.session_state.playlist_history)]
        
        selected_playlist = st.selectbox(
            "Select a playlist to view:",
            options=playlist_options,
            index=0
        )
        
        # Find the selected playlist
        if selected_playlist:
            selected_index = int(selected_playlist.split('.')[0]) - 1
            playlist = st.session_state.playlist_history[selected_index]
            
            # Display the selected playlist
            display_playlist(playlist)
            
            # Option to clear history
            if st.button("Clear All Playlist History"):
                st.session_state.playlist_history = []
                st.experimental_rerun()

# Tab 3: Weather Playlist
with tab3:
    st.header("Weather-Based Playlist")
    
    city = st.text_input("Enter city name:")
    if st.button("Get Weather Playlist"):
        if city:
            with st.spinner("Fetching weather and creating your playlist..."):
                # Get weather-based emotion
                weather_data = get_weather_emotion(city)
                emotion = weather_data["emotion"]
                
                st.write(f"### Weather in {city}:")
                st.write(f"Condition: {weather_data['weather_condition']}")
                st.write(f"Suggested mood: {emotion}")
                
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
                    
                    st.write("### Your Weather Playlist:")
                    
                    # Display tracks
                    for i, track in enumerate(tracks[:10], 1):  # Show first 10 tracks initially
                        st.write(f"{i}. **{track['name']}** by {track['artist']}")
                        if track.get('image_url'):
                            st.image(track['image_url'], width=100)
                        if track.get('external_url'):
                            st.write(f"[Open in Spotify]({track['external_url']})")
                    
                    # Create an expander for the remaining tracks
                    with st.expander("Show more tracks"):
                        for i, track in enumerate(tracks[10:], 11):
                            st.write(f"{i}. **{track['name']}** by {track['artist']}")
                            if track.get('image_url'):
                                st.image(track['image_url'], width=100)
                            if track.get('external_url'):
                                st.write(f"[Open in Spotify]({track['external_url']})")
                    
                    # Create playlist option
                    if st.button("Create Weather Spotify Playlist"):
                        # First get the current user
                        user = get_current_user()
                        if not user:
                            st.error("Please connect to Spotify first")
                            st.info("Note: Creating playlists requires user authentication, which may not be set up in this demo.")
                        else:
                            # Create playlist directly
                            spotify_playlist = create_playlist(
                                user_id=user["id"],
                                playlist_name=playlist["name"],
                                track_ids=[track["id"] for track in tracks if "id" in track],
                                description=f"A playlist based on the weather in {city}: {weather_data['weather_condition']}"
                            )
                            
                            if spotify_playlist:
                                st.success(f"Playlist created! [Open in Spotify]({spotify_playlist['url']})")
                            else:
                                st.error("Failed to create playlist")
                else:
                    st.warning("No recommendations received from Spotify API")
                    st.info("Using mock recommendations instead")
                    
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
                    
                    st.write("### Mock Weather Recommendations:")
                    for i, track in enumerate(mock_tracks[:10], 1):
                        st.write(f"{i}. **{track['name']}** by {track['artist']}")
                    
                    # Create an expander for the remaining tracks
                    with st.expander("Show more tracks"):
                        for i, track in enumerate(mock_tracks[10:], 11):
                            st.write(f"{i}. **{track['name']}** by {track['artist']}")
        else:
            st.warning("Please enter a city name")

# Add troubleshooting section in the sidebar
with st.sidebar:
    with st.expander("Troubleshooting"):
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
        
        if st.button("Run Manual Authentication Test"):
            with st.spinner("Testing authentication..."):
                result = test_spotify_authentication()
                if result:
                    st.success("Authentication test passed successfully!")
                else:
                    st.error("Authentication test failed. Check the console for detailed logs.") 
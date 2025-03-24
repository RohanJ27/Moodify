import os
import sys
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any
import requests

# Load environment variables
load_dotenv()

# Get Spotify credentials from environment variables
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

# Define scopes for Spotify API access
SCOPE = "user-library-read playlist-modify-public user-top-read"

# Emotion to audio features mapping for better recommendations
emotion_features = {
    "happy": {"valence": 0.8, "energy": 0.8, "danceability": 0.7, "tempo": 120},
    "sad": {"valence": 0.2, "energy": 0.3, "danceability": 0.4, "tempo": 80},
    "excited": {"valence": 0.7, "energy": 0.9, "danceability": 0.8, "tempo": 130},
    "calm": {"valence": 0.5, "energy": 0.3, "danceability": 0.4, "tempo": 90},
    "angry": {"valence": 0.3, "energy": 0.9, "danceability": 0.5, "tempo": 140},
    "relaxed": {"valence": 0.6, "energy": 0.3, "danceability": 0.5, "tempo": 85},
    "anxious": {"valence": 0.4, "energy": 0.6, "danceability": 0.5, "tempo": 110},
    "nostalgic": {"valence": 0.6, "energy": 0.4, "danceability": 0.5, "tempo": 95},
    "surprised": {"valence": 0.6, "energy": 0.7, "danceability": 0.6, "tempo": 115},
    "confident": {"valence": 0.7, "energy": 0.7, "danceability": 0.6, "tempo": 110},
    "afraid": {"valence": 0.3, "energy": 0.5, "danceability": 0.4, "tempo": 100},
    "neutral": {"valence": 0.5, "energy": 0.5, "danceability": 0.5, "tempo": 100}
}

def get_spotify_client():
    """
    Create and return a Spotify client using Client Credentials flow.
    This is suitable for API endpoints that don't require user authorization.
    
    Returns:
        spotipy.Spotify: An authenticated Spotify client.
    """
    try:
        # Print credentials status (without revealing actual values)
        if not SPOTIFY_CLIENT_ID:
            print("ERROR: Missing SPOTIFY_CLIENT_ID environment variable")
            return None
        else:
            print(f"SPOTIFY_CLIENT_ID is set (length: {len(SPOTIFY_CLIENT_ID)})")
            
        if not SPOTIFY_CLIENT_SECRET:
            print("ERROR: Missing SPOTIFY_CLIENT_SECRET environment variable")
            return None
        else:
            print(f"SPOTIFY_CLIENT_SECRET is set (length: {len(SPOTIFY_CLIENT_SECRET)})")
            
        print("Creating Spotify client with Client Credentials flow...")
        
        # Use Client Credentials flow for API access (no user login required)
        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        
        # Explicitly get the access token to verify it works
        try:
            access_token = auth_manager.get_access_token(as_dict=False)
            token_prefix = access_token[:10] if access_token else "None"
            print(f"Successfully obtained access token (prefix: {token_prefix}...)")
        except Exception as token_error:
            print(f"Failed to obtain access token: {token_error}")
            return None
        
        client = spotipy.Spotify(auth_manager=auth_manager)
        
        # Test connection with a simple API call
        try:
            # Try to get a simple response from the API to verify the token works
            # Categories is usually a reliable endpoint to test with
            test_response = client.categories(limit=1)
            print(f"Successfully connected to Spotify API (got {len(test_response.get('categories', {}).get('items', []))} categories)")
            return client
        except Exception as e:
            print(f"Error testing Spotify connection: {e}")
            
            # Try an even simpler API call as a last resort
            try:
                print("Trying alternative API endpoint...")
                test_response = client.new_releases(limit=1)
                print("Successfully connected to Spotify API using new_releases endpoint")
                return client
            except Exception as e2:
                print(f"Error with alternative API call: {e2}")
                return None
    
    except Exception as e:
        print(f"Error creating Spotify client: {e}")
        return None

def create_spotify_client():
    """
    Create and return a Spotify client with OAuth authentication flow.
    This is required for user-specific actions like creating playlists.
    
    Returns:
        spotipy.Spotify: Authenticated Spotify client with user authorization.
    """
    try:
        if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI]):
            print("Missing required Spotify credentials in environment variables")
            return None
            
        auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=SCOPE,
            cache_path=".spotifycache"
        )
        
        return spotipy.Spotify(auth_manager=auth_manager)
    
    except Exception as e:
        print(f"Error creating Spotify client: {e}")
        return None

def get_current_user():
    """
    Get the current user's Spotify profile.
    
    Returns:
        dict: User profile information.
    """
    try:
        spotify = create_spotify_client()
        if not spotify:
            return None
            
        user = spotify.current_user()
        return user
    
    except Exception as e:
        print(f"Error getting current user: {e}")
        return None

def get_direct_spotify_recommendations(sp, seed_track=None, seed_genres=None, audio_features=None, limit=10):
    """
    Make a direct API call to Spotify recommendations endpoint to avoid parameter formatting issues.
    
    Args:
        sp (spotipy.Spotify): Spotify client instance
        seed_track (str, optional): A single seed track ID
        seed_genres (list, optional): A list of genre names
        audio_features (dict, optional): Dict of audio features with target values
        limit (int, optional): Number of tracks to return
        
    Returns:
        dict: Raw Spotify API response
    """
    try:
        # Build request URL and parameters manually
        endpoint = "recommendations"
        params = {"limit": min(limit, 100)}
        
        # Add seed parameters - only use ONE of these methods (tracks preferred over genres)
        if seed_track:
            params["seed_tracks"] = seed_track
        elif seed_genres and len(seed_genres) > 0:
            # For seed_genres, join with comma explicitly
            params["seed_genres"] = ",".join(seed_genres[:5])  # Max 5 seed values
        else:
            # Default to a popular genre if nothing provided
            params["seed_genres"] = "pop"
            
        # Add audio features if provided
        if audio_features:
            for feature, value in audio_features.items():
                if value is not None:
                    feature_name = f"target_{feature}"
                    params[feature_name] = max(0.0, min(1.0, float(value)))
                    
        print(f"Making direct API call to recommendations with params: {params}")
        
        # Use the lower-level _get method from spotipy to have more control
        # or construct an alternate approach if it's still not working
        try:
            response = sp._get(endpoint, params)
            # Check if we actually got tracks
            if response and "tracks" in response and len(response["tracks"]) > 0:
                print(f"Successfully got {len(response['tracks'])} tracks from Spotify API")
                return response
            else:
                print("No tracks returned from direct API call")
                return {"tracks": []}
                
        except Exception as e:
            print(f"Direct API call failed: {e}")
            return {"tracks": []}
            
    except Exception as e:
        print(f"Error setting up direct API call: {e}")
        return {"tracks": []}
        
def get_recommendations(seed_genres: List[str], target_valence: float = None, target_energy: float = None, limit: int = 20) -> List[dict]:
    """
    Get track recommendations from Spotify based on seed genres and target audio features.
    
    Args:
        seed_genres (List[str]): List of seed genres to base recommendations on.
        target_valence (float, optional): Target valence value (0.0 to 1.0).
        target_energy (float, optional): Target energy value (0.0 to 1.0).
        limit (int, optional): Maximum number of tracks to recommend. Defaults to 20.
        
    Returns:
        List[dict]: List of recommended tracks, each containing id, name, artist, etc.
    """
    try:
        # Get a Spotify client using client credentials flow
        sp = get_spotify_client()
        if not sp:
            print("Failed to initialize Spotify client")
            return get_mock_recommendations()
        
        # Known valid Spotify genres (reduced to most common ones)
        valid_spotify_genres = [
            "acoustic", "alternative", "ambient", "blues", "chill", "classical", 
            "country", "dance", "electronic", "folk", "funk", "hip-hop", "indie", 
            "jazz", "metal", "pop", "punk", "r-n-b", "reggae", "rock", "soul"
        ]
        
        # Filter provided genres against known valid genres
        valid_genres = [genre for genre in seed_genres if genre in valid_spotify_genres]
        
        # If no valid genres found, use some defaults
        if not valid_genres:
            valid_genres = ["pop", "rock"]
        
        # Limit to at most 5 seed genres
        valid_genres = valid_genres[:5]
        
        print(f"Will use these valid genres: {valid_genres}")
        
        # Prepare audio features
        audio_features = {}
        if target_valence is not None:
            audio_features["valence"] = target_valence
        if target_energy is not None:
            audio_features["energy"] = target_energy
        
        # Try multiple approaches to get recommendations
        results = {"tracks": []}
        
        # First try direct API call with seed_genres
        if valid_genres:
            direct_results = get_direct_spotify_recommendations(
                sp=sp, 
                seed_genres=valid_genres,
                audio_features=audio_features,
                limit=limit
            )
            if direct_results and "tracks" in direct_results and direct_results["tracks"]:
                results = direct_results
            
        # If no results, try with a seed track
        if not results["tracks"]:
            # Use a popular track as seed
            popular_tracks = [
                "4aebBr4xhwYSRkASzCuHGP",  # Adele - Hello
                "3DK6m7It6Pw857FcQftMds",  # Bad Bunny - Tití Me Preguntó
                "7KXjTSCq5nL1LoYtL7XAwS",  # BLACKPINK - Pink Venom
                "0V3wPSX9ygBnCm8psDIegu",  # Taylor Swift - Anti-Hero
                "2LBqCSwhJGcFQeTHMVGwy3"   # The Weeknd - Blinding Lights
            ]
            
            for track_id in popular_tracks:
                direct_results = get_direct_spotify_recommendations(
                    sp=sp,
                    seed_track=track_id,
                    audio_features=audio_features,
                    limit=limit
                )
                if direct_results and "tracks" in direct_results and direct_results["tracks"]:
                    results = direct_results
                    break
        
        # If still no results, try to get some new releases and use one as seed
        if not results["tracks"]:
            try:
                new_releases = sp.new_releases(limit=5)
                if new_releases and "albums" in new_releases and new_releases["albums"]["items"]:
                    # Get a track from the first album
                    album_id = new_releases["albums"]["items"][0]["id"]
                    album_tracks = sp.album_tracks(album_id, limit=1)
                    if album_tracks and "items" in album_tracks and album_tracks["items"]:
                        track_id = album_tracks["items"][0]["id"]
                        
                        direct_results = get_direct_spotify_recommendations(
                            sp=sp,
                            seed_track=track_id,
                            audio_features=audio_features,
                            limit=limit
                        )
                        if direct_results and "tracks" in direct_results and direct_results["tracks"]:
                            results = direct_results
            except Exception as e:
                print(f"Error getting new releases: {e}")
        
        # If still no tracks, return mock data
        if not results["tracks"]:
            print("All API approaches failed, returning mock data")
            return get_mock_recommendations(emotion_type="neutral")
        
        # Format the response
        tracks = []
        for track in results["tracks"]:
            tracks.append({
                "id": track["id"],
                "name": track["name"],
                "artist": track["artists"][0]["name"] if track.get("artists") else "Unknown Artist",
                "album": track.get("album", {}).get("name", "Unknown Album"),
                "image_url": track.get("album", {}).get("images", [{}])[0].get("url") if track.get("album", {}).get("images") else None,
                "preview_url": track.get("preview_url"),
                "external_url": track.get("external_urls", {}).get("spotify", "https://spotify.com")
            })
            
        if tracks:
            print(f"Successfully retrieved {len(tracks)} track recommendations")
            return tracks
        else:
            print("No tracks found in the Spotify response")
            return get_mock_recommendations(emotion_type="neutral")
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return get_mock_recommendations(emotion_type="neutral")

def get_mock_recommendations(emotion_type="happy"):
    """
    Return mock recommendations based on emotion type
    
    Args:
        emotion_type (str): Type of emotion to match recommendations to
        
    Returns:
        List[dict]: List of mock track recommendations
    """
    print(f"Returning mock {emotion_type} recommendations")
    
    # Different sets of mock data for different emotions
    mock_data = {
        "happy": [
            {
                "id": "mock1",
                "name": "Happy Song",
                "artist": "Demo Artist",
                "album": "Demo Album",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273b52c71f8378f6eb57b7e7ffa",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh"
            },
            {
                "id": "mock2",
                "name": "Cheerful Tune",
                "artist": "Sample Artist",
                "album": "Sample Album",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273b52c71f8378f6eb57b7e7ffa",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/1301WleyT98MSxVHPZCA6M"
            },
            {
                "id": "mock3",
                "name": "Upbeat Melody",
                "artist": "Test Artist",
                "album": "Test Album",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273b52c71f8378f6eb57b7e7ffa",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/0HUTL8i4y4MiGCPB5fHuPW"
            }
        ],
        "sad": [
            {
                "id": "mock4",
                "name": "Melancholy",
                "artist": "Sad Artist",
                "album": "Reflections",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273b52c71f8378f6eb57b7e7ffa",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/7qiZfU4dY1lWllzX7mPBI3"
            },
            {
                "id": "mock5",
                "name": "Blue Thoughts",
                "artist": "Tearful Singer",
                "album": "Memories",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273b52c71f8378f6eb57b7e7ffa",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/0VgkVdmE4gld66l8iyGjgx"
            }
        ],
        "neutral": [
            {
                "id": "mock6",
                "name": "Default Track",
                "artist": "Default Artist",
                "album": "Default Album",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273b52c71f8378f6eb57b7e7ffa",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/0c6xIDDpzE81m2q797ordA"
            },
            {
                "id": "mock7",
                "name": "Generic Song",
                "artist": "Generic Artist",
                "album": "Generic Album",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273b52c71f8378f6eb57b7e7ffa",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/0c6xIDDpzE81m2q797ordA"
            }
        ]
    }
    
    # Return appropriate mock data or default to neutral
    return mock_data.get(emotion_type, mock_data["neutral"])

def search_tracks_by_mood(mood: str, limit: int = 10) -> List[dict]:
    """
    Search for tracks on Spotify based on mood using the Search endpoint.
    
    This function maps common moods to relevant search keywords and uses Spotify's 
    Search API to find tracks that match these keywords. It's designed as an alternative
    to the Recommendations API which is restricted for new applications.
    
    Args:
        mood (str): The mood to search tracks for (e.g., "happy", "sad", "calm").
        limit (int, optional): Maximum number of tracks to return. Defaults to 10.
        
    Returns:
        List[dict]: List of tracks, each containing:
            - id: Spotify track ID
            - name: Track name
            - artist: Artist name
            - album: Album name
            - image_url: URL to album cover
            - preview_url: URL to audio preview (if available)
            - external_url: URL to the track on Spotify
    """
    try:
        print(f"Searching for tracks matching mood: {mood}")
        
        # Map moods to search keywords
        mood_keywords = {
            "happy": "happy upbeat cheerful feel good positive uplifting",
            "sad": "sad melancholy emotional ballad heartbreak somber",
            "angry": "angry intense aggressive powerful hard rock metal",
            "calm": "calm peaceful relaxing ambient chill soothing",
            "energetic": "energetic dance upbeat party workout energizing",
            "anxious": "atmospheric tense instrumental suspense",
            "relaxed": "chill lofi acoustic relaxing easy listening",
            "nostalgic": "nostalgic retro vintage classic throwback",
            "romantic": "love romantic sensual smooth r&b ballad",
            "confident": "confident empowering anthem motivational",
            "fearful": "eerie haunting dark suspenseful",
            "surprised": "surprising unexpected quirky unusual",
            "neutral": "pop indie mainstream moderate tempo",
            "stressed": "calming meditation gentle piano instrumental",
            "excited": "exciting upbeat dance party celebration",
            # Add more mood mappings as needed
        }
        
        # Get keywords for the specified mood, or use a default set
        keywords = mood_keywords.get(mood.lower(), "pop rock indie")
        print(f"Using search keywords: {keywords}")
        
        # Get Spotify client
        sp = get_spotify_client()
        if not sp:
            print("Failed to initialize Spotify client")
            return get_mock_recommendations(mood)
        
        # Prepare the search query
        # Format: "keyword1 keyword2" to find tracks matching ANY of the keywords
        search_query = keywords
        
        # Add genre qualifiers to improve results
        genres_by_mood = {
            "happy": "genre:pop genre:dance",
            "sad": "genre:indie genre:folk",
            "angry": "genre:rock genre:metal",
            "calm": "genre:ambient genre:classical",
            "energetic": "genre:dance genre:electronic",
            "relaxed": "genre:acoustic genre:chill",
            # Add more as needed
        }
        
        # Add genre qualifier if available for this mood
        mood_genre = genres_by_mood.get(mood.lower(), "")
        if mood_genre:
            search_query += f" {mood_genre}"
        
        print(f"Final search query: {search_query}")
        
        # Make direct API call to search endpoint
        # Get a fresh token using the existing auth manager
        token = sp._auth_manager.get_access_token(as_dict=False)
        
        # Set up headers with the token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Build query parameters
        params = {
            "q": search_query,
            "type": "track",
            "limit": min(limit, 50),  # Spotify accepts max 50 items for search
            "market": "US"  # Ensure we get playable tracks
        }
        
        # Make the direct API request
        print(f"Making direct request to Spotify Search API with params: {params}")
        response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=params
        )
        
        # Check for successful response
        if response.status_code == 200:
            results = response.json()
            
            # Check if we got tracks
            if results and "tracks" in results and "items" in results["tracks"]:
                items = results["tracks"]["items"]
                print(f"Found {len(items)} tracks matching the mood")
                
                # Format the response
                tracks = []
                for item in items:
                    # Extract the relevant information
                    track = {
                        "id": item["id"],
                        "name": item["name"],
                        "artist": item["artists"][0]["name"] if item.get("artists") else "Unknown Artist",
                        "album": item.get("album", {}).get("name", "Unknown Album"),
                        "image_url": item.get("album", {}).get("images", [{}])[0].get("url") if item.get("album", {}).get("images") else None,
                        "preview_url": item.get("preview_url"),
                        "external_url": item.get("external_urls", {}).get("spotify", "https://spotify.com")
                    }
                    tracks.append(track)
                
                if tracks:
                    return tracks
        
        # If the search fails or returns no results, try with just the mood itself
        print(f"Initial search failed or returned no results. Trying with mood keyword only.")
        
        simple_params = {
            "q": mood,  # Just use the mood itself
            "type": "track",
            "limit": min(limit, 50),
            "market": "US"
        }
        
        simple_response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params=simple_params
        )
        
        if simple_response.status_code == 200:
            simple_results = simple_response.json()
            
            if simple_results and "tracks" in simple_results and "items" in simple_results["tracks"]:
                simple_items = simple_results["tracks"]["items"]
                print(f"Found {len(simple_items)} tracks using simple mood search")
                
                simple_tracks = []
                for item in simple_items:
                    # Extract the relevant information
                    track = {
                        "id": item["id"],
                        "name": item["name"],
                        "artist": item["artists"][0]["name"] if item.get("artists") else "Unknown Artist",
                        "album": item.get("album", {}).get("name", "Unknown Album"),
                        "image_url": item.get("album", {}).get("images", [{}])[0].get("url") if item.get("album", {}).get("images") else None,
                        "preview_url": item.get("preview_url"),
                        "external_url": item.get("external_urls", {}).get("spotify", "https://spotify.com")
                    }
                    simple_tracks.append(track)
                
                if simple_tracks:
                    return simple_tracks
        
        # If all searches fail, fall back to mock data
        print(f"All search attempts failed. Returning mock data for mood: {mood}")
        return get_mock_recommendations(mood)
        
    except Exception as e:
        print(f"Error searching for tracks by mood: {e}")
        return get_mock_recommendations(mood)

def get_recommendations_by_emotion(emotion: str, limit: int = 10) -> List[dict]:
    """
    Get track recommendations based on emotion.
    
    This function uses the search_tracks_by_mood function to find tracks that match
    the specified emotion, as a replacement for the now-restricted Recommendations API.
    
    Args:
        emotion (str): The emotion to base recommendations on.
        limit (int, optional): Number of tracks to recommend. Defaults to 10.
        
    Returns:
        List[dict]: List of recommended tracks.
    """
    print(f"Getting tracks for emotion: {emotion}")
    
    try:
        # Map emotion to corresponding audio features
        features = emotion_features.get(emotion.lower(), emotion_features["neutral"])
        
        # Use our new search-based approach to find tracks by mood
        tracks = search_tracks_by_mood(emotion, limit=limit)
        
        # If we got tracks back (and not empty list), return them
        if tracks:
            print(f"Found {len(tracks)} tracks for emotion: {emotion}")
            return tracks
            
        # Fall back to mock data if search failed
        print(f"Search failed for emotion: {emotion}. Using mock data.")
        return get_mock_recommendations(emotion)
        
    except Exception as e:
        print(f"Error getting recommendations by emotion: {e}")
        return get_mock_recommendations(emotion)

def create_playlist(user_id, playlist_name, track_ids, description=None):
    """
    Create a new playlist for the user with the given tracks.
    
    Args:
        user_id (str): The user's Spotify ID.
        playlist_name (str): Name for the new playlist.
        track_ids (list): List of Spotify track IDs to add to the playlist.
        description (str, optional): Description for the playlist.
        
    Returns:
        dict: Playlist information including ID and URL.
    """
    try:
        spotify = create_spotify_client()
        if not spotify:
            return None
            
        # Create an empty playlist
        playlist = spotify.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=True,
            description=description or f"Created by Mood & Weather Playlist Creator"
        )
        
        # Add tracks to the playlist
        if track_ids:
            spotify.playlist_add_items(playlist["id"], track_ids)
            
        # Return playlist info
        return {
            "id": playlist["id"],
            "name": playlist["name"],
            "url": playlist["external_urls"]["spotify"],
            "tracks_count": len(track_ids)
        }
    
    except Exception as e:
        print(f"Error creating playlist: {e}")
        return None

def search_track(query, limit=5):
    """
    Search for tracks on Spotify.
    
    Args:
        query (str): Search query (e.g., song name, artist, etc.)
        limit (int): Maximum number of results to return
        
    Returns:
        list: List of matching track data
    """
    try:
        # Get the Spotify client
        client = get_spotify_client()
        if not client:
            return {"error": "Failed to connect to Spotify"}
        
        results = client.search(q=query, type="track", limit=limit)
        
        tracks = []
        for item in results["tracks"]["items"]:
            track = {
                "id": item["id"],
                "name": item["name"],
                "artist": item["artists"][0]["name"],
                "album": item["album"]["name"],
                "image_url": item["album"]["images"][0]["url"] if item["album"]["images"] else None,
                "preview_url": item["preview_url"],
                "external_url": item["external_urls"]["spotify"]
            }
            tracks.append(track)
            
        return tracks
    
    except Exception as e:
        print(f"Error searching for tracks: {e}")
        return []

def get_track_info(track_id):
    """
    Get information about a specific Spotify track.
    
    Args:
        track_id (str): Spotify track ID
        
    Returns:
        dict: Track information
    """
    try:
        client = get_spotify_client()
        if not client:
            return {"error": "Failed to connect to Spotify"}
        
        track = client.track(track_id)
        
        return {
            "id": track["id"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "preview_url": track["preview_url"],
            "external_url": track["external_urls"]["spotify"]
        }
    
    except Exception as e:
        print(f"Error getting track info: {e}")
        return {}

def generate_playlist_from_tracks(track_ids, playlist_name, description=None):
    """
    Create a playlist from a list of tracks.
    
    Args:
        track_ids (list): List of Spotify track IDs
        playlist_name (str): Name for the playlist
        description (str, optional): Description for the playlist
        
    Returns:
        dict: Playlist information including URL
    """
    try:
        # Get the current user
        user = get_current_user()
        if not user:
            return {"error": "Failed to get user information"}
        
        # Create the playlist
        playlist = create_playlist(
            user_id=user["id"],
            playlist_name=playlist_name,
            track_ids=track_ids,
            description=description
        )
        
        return playlist
    
    except Exception as e:
        print(f"Error generating playlist: {e}")
        return {"error": f"Failed to create playlist: {str(e)}"}

def spotify_api_health_check():
    """
    Comprehensive health check of the Spotify API integration.
    
    This function tests all key aspects of the Spotify API integration
    and returns a detailed status report.
    
    Returns:
        dict: API health status
    """
    results = {
        "success": False,
        "messages": [],
        "env_vars_set": False
    }
    
    # Check environment variables
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    if not client_id:
        results["messages"].append("❌ SPOTIFY_CLIENT_ID is missing")
    else:
        results["messages"].append(f"✓ SPOTIFY_CLIENT_ID is set (length: {len(client_id)})")
    
    if not client_secret:
        results["messages"].append("❌ SPOTIFY_CLIENT_SECRET is missing")
    else:
        results["messages"].append(f"✓ SPOTIFY_CLIENT_SECRET is set (length: {len(client_secret)})")
    
    if not redirect_uri:
        results["messages"].append("⚠️ SPOTIFY_REDIRECT_URI is not set, using default")
    else:
        results["messages"].append(f"✓ SPOTIFY_REDIRECT_URI is set: {redirect_uri}")
    
    # Mark if environment variables are set
    results["env_vars_set"] = bool(client_id and client_secret)
    
    if not results["env_vars_set"]:
        results["messages"].append("❌ Required environment variables are missing")
        return results
    
    # Test client credentials flow
    try:
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        
        try:
            access_token = auth_manager.get_access_token(as_dict=False)
            if access_token:
                token_prefix = access_token[:10] if access_token else "None"
                results["messages"].append(f"✓ Successfully obtained access token (prefix: {token_prefix}...)")
            else:
                results["messages"].append("❌ No access token returned")
                return results
        except Exception as token_error:
            results["messages"].append(f"❌ Failed to obtain access token: {token_error}")
            return results
        
        client = spotipy.Spotify(auth_manager=auth_manager)
        
        # Test public API endpoints
        try:
            # Try to access the categories endpoint
            response = client.categories(limit=1)
            if response and 'categories' in response:
                results["messages"].append(f"✓ Successfully accessed categories endpoint")
            else:
                results["messages"].append("❌ Categories endpoint returned unexpected data")
        except Exception as api_error:
            results["messages"].append(f"❌ Categories endpoint access failed: {api_error}")
            
            # Try one more endpoint
            try:
                results["messages"].append("Trying alternative endpoint (new releases)...")
                response = client.new_releases(limit=1)
                results["messages"].append("✓ Successfully accessed new releases endpoint")
            except Exception as e2:
                results["messages"].append(f"❌ New releases endpoint also failed: {e2}")
                return results
        
        # Test search endpoint
        try:
            search_response = client.search(q="happy", type="track", limit=1)
            if search_response and 'tracks' in search_response and 'items' in search_response['tracks']:
                results["messages"].append(f"✓ Successfully searched for tracks with the Search API")
                results["success"] = True
            else:
                results["messages"].append("❌ Search API returned unexpected data format")
        except Exception as search_error:
            results["messages"].append(f"❌ Search API access failed: {search_error}")
            results["success"] = False
            
        # Add note about Recommendations API restrictions
        results["messages"].append(
            "ℹ️ NOTE: The Spotify Recommendations API is now restricted for new applications. "
            "We're using the Search API as a viable alternative."
        )
        
    except Exception as e:
        results["messages"].append(f"❌ Error setting up Spotify client: {e}")
    
    return results

def test_spotify_authentication():
    """
    Test Spotify API authentication and print detailed diagnostic information.
    
    Returns:
        bool: True if authentication successful, False otherwise
    """
    print("\n==== SPOTIFY API AUTHENTICATION TEST ====")
    
    # Check if environment variables are set
    print("\nChecking environment variables:")
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    if not client_id:
        print("❌ SPOTIFY_CLIENT_ID is missing")
        return False
    else:
        print(f"✓ SPOTIFY_CLIENT_ID is set (length: {len(client_id)})")
    
    if not client_secret:
        print("❌ SPOTIFY_CLIENT_SECRET is missing")
        return False
    else:
        print(f"✓ SPOTIFY_CLIENT_SECRET is set (length: {len(client_secret)})")
    
    if not redirect_uri:
        print("⚠️ SPOTIFY_REDIRECT_URI is not set, using default: http://localhost:8888/callback")
    else:
        print(f"✓ SPOTIFY_REDIRECT_URI is set: {redirect_uri}")
    
    # Test Client Credentials flow
    print("\nTesting Client Credentials flow (for non-user endpoints):")
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        
        try:
            access_token = auth_manager.get_access_token(as_dict=False)
            if access_token:
                token_prefix = access_token[:10] if access_token else "None"
                print(f"✓ Successfully obtained access token (prefix: {token_prefix}...)")
            else:
                print("❌ No access token returned")
                return False
        except Exception as token_error:
            print(f"❌ Failed to obtain access token: {token_error}")
            return False
        
        client = spotipy.Spotify(auth_manager=auth_manager)
        
        # Try accessing a public endpoint that doesn't require user authorization
        try:
            response = client.categories(limit=1)
            if response and 'categories' in response:
                print(f"✓ Successfully made API call to categories endpoint")
            else:
                print("❌ API response does not contain expected data")
                return False
        except Exception as api_error:
            print(f"❌ API call failed: {api_error}")
            
            # Try one more endpoint
            try:
                print("Trying alternative endpoint (new releases)...")
                response = client.new_releases(limit=1)
                print("✓ Successfully made API call to new releases endpoint")
            except Exception as e2:
                print(f"❌ Alternative API call also failed: {e2}")
                return False
        
        # Test Search API
        try:
            print("\nTesting Search API:")
            search_response = client.search(q="happy", type="track", limit=1)
            if search_response and 'tracks' in search_response and 'items' in search_response['tracks']:
                track_count = len(search_response['tracks']['items'])
                print(f"✓ Successfully searched for tracks with keyword 'happy' ({track_count} results)")
            else:
                print("❌ Search API returned unexpected format")
        except Exception as search_error:
            print(f"❌ Search API test failed: {search_error}")
    
    except Exception as e:
        print(f"❌ Error setting up Spotify client: {e}")
        return False
    
    print("\n✓ Spotify API authentication test PASSED")
    print("==== END OF TEST ====\n")
    return True 
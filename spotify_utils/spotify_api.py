import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any
import random
import requests
from itertools import cycle

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
    "angry": {"valence": 0.3, "energy": 0.9, "danceability": 0.5, "tempo": 140},
    "calm": {"valence": 0.6, "energy": 0.3, "danceability": 0.4, "tempo": 90},
    "excited": {"valence": 0.8, "energy": 0.9, "danceability": 0.8, "tempo": 130},
    "anxious": {"valence": 0.4, "energy": 0.7, "danceability": 0.5, "tempo": 110},
    "peaceful": {"valence": 0.7, "energy": 0.2, "danceability": 0.3, "tempo": 70},
    "energetic": {"valence": 0.7, "energy": 0.9, "danceability": 0.8, "tempo": 125},
    "melancholic": {"valence": 0.3, "energy": 0.4, "danceability": 0.3, "tempo": 85},
    "reflective": {"valence": 0.5, "energy": 0.3, "danceability": 0.3, "tempo": 95},
    "intense": {"valence": 0.4, "energy": 0.8, "danceability": 0.6, "tempo": 135},
    "thoughtful": {"valence": 0.5, "energy": 0.4, "danceability": 0.4, "tempo": 100},
    "mysterious": {"valence": 0.4, "energy": 0.5, "danceability": 0.5, "tempo": 105},
    "dreamy": {"valence": 0.6, "energy": 0.4, "danceability": 0.5, "tempo": 95},
    "introspective": {"valence": 0.5, "energy": 0.3, "danceability": 0.3, "tempo": 90},
    "irritated": {"valence": 0.3, "energy": 0.7, "danceability": 0.5, "tempo": 115},
    "turbulent": {"valence": 0.3, "energy": 0.8, "danceability": 0.6, "tempo": 130},
    "fearful": {"valence": 0.2, "energy": 0.6, "danceability": 0.4, "tempo": 100},
    "neutral": {"valence": 0.5, "energy": 0.5, "danceability": 0.5, "tempo": 100}
}

# Define mood keywords with synonyms for diversified searches
mood_keywords = {
    "happy": ["joyful", "cheerful", "uplifting", "sunshine", "blissful", "happy", "upbeat", "feel good", "positive"],
    "sad": ["melancholy", "blue", "heartbroken", "somber", "downcast", "sad", "emotional", "heartache", "gloomy"],
    "angry": ["furious", "rage", "intense", "aggressive", "fierce", "angry", "powerful", "rebellious", "frustration"],
    "calm": ["peaceful", "tranquil", "serene", "gentle", "soothing", "calm", "relaxed", "meditative", "chill"],
    "energetic": ["lively", "dynamic", "vibrant", "spirited", "energizing", "energetic", "bouncy", "upbeat", "workout"],
    "anxious": ["tense", "nervous", "worried", "uneasy", "restless", "anxious", "apprehensive", "edgy", "dramatic"],
    "relaxed": ["mellow", "laid-back", "easygoing", "comfortable", "cozy", "relaxed", "chill", "easy listening", "smooth"],
    "nostalgic": ["reminiscent", "retro", "vintage", "throwback", "memory", "nostalgic", "classic", "oldies", "timeless"],
    "romantic": ["love", "affectionate", "passionate", "dreamy", "tender", "romantic", "intimate", "sensual", "loving"],
    "confident": ["empowered", "strong", "bold", "fearless", "assured", "confident", "pride", "powerful", "motivational"],
    "fearful": ["scared", "frightened", "eerie", "haunting", "suspenseful", "fearful", "ominous", "spooky", "creepy"],
    "surprised": ["astonished", "unexpected", "amazed", "shocked", "stunned", "surprising", "quirky", "unusual", "wonder"],
    "neutral": ["balanced", "moderate", "middle", "standard", "regular", "neutral", "ordinary", "casual", "everyday"],
    "stressed": ["pressured", "overwhelmed", "tense", "frantic", "rushed", "stressed", "urgent", "hectic", "chaotic"]
}

# Genre mapping by mood for better search results
genre_by_mood = {
    "happy": ["pop", "dance", "disco", "funk", "electronic"],
    "sad": ["indie", "folk", "blues", "soul", "alternative"],
    "angry": ["rock", "metal", "punk", "hardcore", "grunge"],
    "calm": ["ambient", "classical", "acoustic", "piano", "instrumental"],
    "energetic": ["dance", "electronic", "house", "techno", "edm"],
    "anxious": ["alternative", "rock", "electronic", "experimental", "indie"],
    "relaxed": ["chill", "lofi", "acoustic", "ambient", "jazz"],
    "nostalgic": ["oldies", "80s", "70s", "classic rock", "retro"],
    "romantic": ["r&b", "soul", "jazz", "pop", "acoustic"],
    "confident": ["hip-hop", "pop", "dance", "rock", "r&b"],
    "fearful": ["soundtrack", "experimental", "ambient", "classical", "instrumental"],
    "surprised": ["electronic", "indie", "experimental", "alternative", "fusion"],
    "neutral": ["pop", "rock", "indie", "alternative", "mainstream"],
    "stressed": ["ambient", "classical", "instrumental", "meditation", "piano"]
}

def get_spotify_client():
    """
    Create and return a Spotify client with Client Credentials flow authentication.
    This is suitable for API endpoints that don't require user authorization.
    
    Returns:
        spotipy.Spotify: Authenticated Spotify client.
    """
    try:
        # Print status of credentials (without revealing values)
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
        
        # Explicitly get and verify the access token
        try:
            access_token = auth_manager.get_access_token(as_dict=False)
            token_prefix = access_token[:10] if access_token else "None"
            print(f"Successfully obtained access token (prefix: {token_prefix}...)")
        except Exception as token_error:
            print(f"Failed to obtain access token: {token_error}")
            return None
        
        # Create Spotify client with the verified token
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Test connection with a simple API call
        try:
            test_response = sp.categories(limit=1)
            print(f"Successfully connected to Spotify API (got {len(test_response.get('categories', {}).get('items', []))} categories)")
            return sp
        except Exception as e:
            print(f"Error testing Spotify connection: {e}")
            return None
    
    except Exception as e:
        print(f"Error creating Spotify client: {e}")
        return None

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
    
    # Test Client Credentials flow (for recommendations API)
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
        
        # Try direct HTTP request to recommendations endpoint
        print("\nTesting direct HTTP request to recommendations endpoint:")
        
        # Get a fresh token
        token = auth_manager.get_access_token(as_dict=False)
        
        # Set up headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test params with seed_genres
        params = {
            "limit": 1,
            "seed_genres": "pop"
        }
        
        try:
            print(f"Making request with params: {params}")
            response = requests.get(
                "https://api.spotify.com/v1/recommendations",
                headers=headers,
                params=params
            )
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data and "tracks" in data:
                    track_count = len(data["tracks"])
                    print(f"✓ Successfully received {track_count} tracks from recommendations endpoint")
                else:
                    print("❌ No tracks in response")
            else:
                print(f"❌ Recommendations API returned error: {response.status_code}")
                print(f"Error details: {response.text}")
                
                # Try with seed_artists instead
                print("\nTrying with seed_artists instead:")
                artist_params = {
                    "limit": 1,
                    "seed_artists": "4NHQUGzhtTLFvgF5SZesLK"  # Drake
                }
                
                artist_response = requests.get(
                    "https://api.spotify.com/v1/recommendations",
                    headers=headers,
                    params=artist_params
                )
                
                print(f"Response status code: {artist_response.status_code}")
                
                if artist_response.status_code == 200:
                    artist_data = artist_response.json()
                    if artist_data and "tracks" in artist_data:
                        track_count = len(artist_data["tracks"])
                        print(f"✓ Successfully received {track_count} tracks using seed_artists")
                    else:
                        print("❌ No tracks in response using seed_artists")
                else:
                    print(f"❌ Recommendations API with seed_artists returned error: {artist_response.status_code}")
                    print(f"Error details: {artist_response.text}")
        
        except Exception as rec_error:
            print(f"❌ Error testing recommendations endpoint: {rec_error}")
    
    except Exception as e:
        print(f"❌ Error setting up Spotify client: {e}")
        return False
    
    print("\n✓ Spotify API authentication test PASSED")
    print("==== END OF TEST ====\n")
    return True

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
        
        sp = spotipy.Spotify(auth_manager=auth_manager)
        return sp
    
    except Exception as e:
        print(f"Error creating Spotify client: {e}")
        return None

def get_recommendations(seed_genres: List[str], target_valence: float = None, target_energy: float = None, limit: int = 20) -> List[dict]:
    """
    Get track recommendations from Spotify based on seed genres and target audio features.
    
    This function uses the Spotify Recommendations API to generate a playlist based on 
    the provided seed genres and audio features that match the user's mood.
    
    For example:
    - Happy mood: target_valence=0.8, target_energy=0.8
    - Sad mood: target_valence=0.2, target_energy=0.3
    - Energetic mood: target_valence=0.6, target_energy=0.9
    
    Args:
        seed_genres (List[str]): List of seed genres to base recommendations on.
            Examples: ["pop", "dance"], ["rock", "alternative"], ["classical"]
        target_valence (float, optional): Target valence value (0.0 to 1.0).
            Higher values indicate more positive/happy mood.
        target_energy (float, optional): Target energy value (0.0 to 1.0).
            Higher values indicate more energetic tracks.
        limit (int, optional): Maximum number of tracks to recommend. Defaults to 20.
        
    Returns:
        List[dict]: List of recommended tracks, each containing:
            - id: Spotify track ID
            - name: Track name
            - artist: Artist name
            - album: Album name
            - image_url: URL to album cover
            - preview_url: URL to audio preview (if available)
            - external_url: URL to the track on Spotify
    """
    try:
        # Log the incoming parameters
        print(f"Making Spotify recommendations request with params: {{" +
              f"'limit': {limit}, " +
              f"'seed_genres': '{','.join(seed_genres)}', " +
              f"'target_valence': {target_valence}, " +
              f"'target_energy': {target_energy}}}")
        
        # Get a Spotify client using client credentials flow
        sp = get_spotify_client()
        if not sp:
            print("Failed to initialize Spotify client")
            return get_mock_recommendations()
        
        # Known valid Spotify genres to filter against
        valid_spotify_genres = [
            "acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "anime", 
            "black-metal", "bluegrass", "blues", "bossanova", "brazil", "breakbeat", 
            "british", "cantopop", "chicago-house", "children", "chill", "classical", 
            "club", "comedy", "country", "dance", "dancehall", "death-metal", "deep-house", 
            "detroit-techno", "disco", "disney", "drum-and-bass", "dub", "dubstep", 
            "edm", "electro", "electronic", "emo", "folk", "forro", "french", "funk", 
            "garage", "german", "gospel", "goth", "grindcore", "groove", "grunge", 
            "guitar", "happy", "hard-rock", "hardcore", "hardstyle", "heavy-metal", 
            "hip-hop", "holidays", "honky-tonk", "house", "idm", "indian", "indie", 
            "indie-pop", "industrial", "iranian", "j-dance", "j-idol", "j-pop", "j-rock", 
            "jazz", "k-pop", "kids", "latin", "latino", "malay", "mandopop", "metal", 
            "metal-misc", "metalcore", "minimal-techno", "movies", "mpb", "new-age", 
            "new-release", "opera", "pagode", "party", "philippines-opm", "piano", "pop", 
            "pop-film", "post-dubstep", "power-pop", "progressive-house", "psych-rock", 
            "punk", "punk-rock", "r-n-b", "rainy-day", "reggae", "reggaeton", "road-trip", 
            "rock", "rock-n-roll", "rockabilly", "romance", "sad", "salsa", "samba", 
            "sertanejo", "show-tunes", "singer-songwriter", "ska", "sleep", "songwriter", 
            "soul", "soundtracks", "spanish", "study", "summer", "swedish", "synth-pop", 
            "tango", "techno", "trance", "trip-hop", "turkish", "work-out", "world-music"
        ]
        
        # Filter provided genres against known valid genres
        valid_genres = [genre for genre in seed_genres if genre in valid_spotify_genres]
        
        # If no valid genres found, use some defaults
        if not valid_genres:
            print("No valid genres found. Using default genres.")
            valid_genres = ["pop", "rock"]
        
        # Limit to at most 5 seed genres as per Spotify API limitation
        valid_genres = valid_genres[:5]
        
        print(f"Using valid genres: {valid_genres}")
        
        # IMPORTANT: We'll bypass the spotipy library for the recommendations call
        # since it seems to be formatting the seed_genres parameter incorrectly
        
        # Use the requests library directly to make the API call
        
        # Get a fresh token using the existing auth manager
        token = sp._auth_manager.get_access_token(as_dict=False)
        
        # Set up headers with the token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Build query parameters
        params = {
            "limit": min(limit, 100),  # Spotify accepts max 100 tracks
            "seed_genres": ",".join(valid_genres)  # Correctly join with commas
        }
        
        # Add audio features if provided
        if target_valence is not None:
            params["target_valence"] = max(0.0, min(1.0, target_valence))
            
        if target_energy is not None:
            params["target_energy"] = max(0.0, min(1.0, target_energy))
        
        # Make the direct API request
        print(f"Making direct request to Spotify API with params: {params}")
        response = requests.get(
            "https://api.spotify.com/v1/recommendations",
            headers=headers,
            params=params
        )
        
        # Check for successful response
        if response.status_code == 200:
            results = response.json()
            
            # Check if we got tracks
            if results and "tracks" in results and results["tracks"]:
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
                
                print(f"Successfully retrieved {len(tracks)} track recommendations")
                return tracks
        
        # If direct request fails or returns no tracks, try with a seed track
        print(f"Direct request failed with status {response.status_code}. Trying with seed tracks.")
        
        # Try using a popular track as a seed
        try:
            # Define some popular track IDs to try as seeds
            popular_tracks = [
                "4aebBr4xhwYSRkASzCuHGP",  # Adele - Hello
                "3DK6m7It6Pw857FcQftMds",  # Bad Bunny - Tití Me Preguntó
                "7KXjTSCq5nL1LoYtL7XAwS",  # BLACKPINK - Pink Venom
                "0V3wPSX9ygBnCm8psDIegu",  # Taylor Swift - Anti-Hero
                "2LBqCSwhJGcFQeTHMVGwy3"   # The Weeknd - Blinding Lights
            ]
            
            # Try each popular track as a seed
            for track_id in popular_tracks:
                # Update params to use seed track instead of genres
                track_params = {
                    "limit": min(limit, 100),
                    "seed_tracks": track_id
                }
                
                # Add audio features if provided
                if target_valence is not None:
                    track_params["target_valence"] = max(0.0, min(1.0, target_valence))
                    
                if target_energy is not None:
                    track_params["target_energy"] = max(0.0, min(1.0, target_energy))
                
                # Make the API request with a seed track
                print(f"Trying with seed track: {track_id}")
                track_response = requests.get(
                    "https://api.spotify.com/v1/recommendations",
                    headers=headers,
                    params=track_params
                )
                
                # Check if successful
                if track_response.status_code == 200:
                    track_results = track_response.json()
                    
                    # Check if we got tracks
                    if track_results and "tracks" in track_results and track_results["tracks"]:
                        # Format the response
                        tracks = []
                        for track in track_results["tracks"]:
                            tracks.append({
                                "id": track["id"],
                                "name": track["name"],
                                "artist": track["artists"][0]["name"] if track.get("artists") else "Unknown Artist",
                                "album": track.get("album", {}).get("name", "Unknown Album"),
                                "image_url": track.get("album", {}).get("images", [{}])[0].get("url") if track.get("album", {}).get("images") else None,
                                "preview_url": track.get("preview_url"),
                                "external_url": track.get("external_urls", {}).get("spotify", "https://spotify.com")
                            })
                        
                        print(f"Successfully retrieved {len(tracks)} track recommendations using seed track")
                        return tracks
                else:
                    print(f"Seed track request failed with status {track_response.status_code}")
        
        except Exception as track_error:
            print(f"Error trying seed track approach: {track_error}")
        
        # If all methods fail, return mock data
        print("All API approaches failed, returning mock data")
        return get_mock_recommendations()
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return get_mock_recommendations()

def get_mock_recommendations(emotion_type="happy"):
    """
    Return enhanced mock recommendations based on emotion type.
    Used when the Spotify API fails or due to Spotify API limitations for new applications.
    
    Note: As of November 2023, Spotify has restricted access to the Recommendations
    endpoint for new Web API applications, leading to 404 errors. This function provides 
    a fallback with emotion-appropriate mock data.
    
    Args:
        emotion_type (str): Type of emotion to match recommendations to
        
    Returns:
        List[dict]: List of mock track recommendations
    """
    print(f"Returning enhanced mock {emotion_type} recommendations")
    
    # Common mock data structure with different tracks for different emotions
    mock_data = {
        "happy": [
            {
                "id": "happy1",
                "name": "Happy",
                "artist": "Pharrell Williams",
                "album": "G I R L",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273e8107e6d9214baa81bb79bba",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/60nZcImufyMA1MKQY3dcCH"
            },
            {
                "id": "happy2",
                "name": "Can't Stop the Feeling!",
                "artist": "Justin Timberlake",
                "album": "Trolls (Original Motion Picture Soundtrack)",
                "image_url": "https://i.scdn.co/image/ab67616d0000b2738376f28c2dbd34213c0e6882",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/1WkMMavIMc4JZ8cfMmxHkI"
            },
            {
                "id": "happy3",
                "name": "Walking on Sunshine",
                "artist": "Katrina & The Waves",
                "album": "Katrina & The Waves",
                "image_url": "https://i.scdn.co/image/ab67616d0000b2736b048063ef3329ea7bbfd7f2",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/05wIrZSwuaVWhcv5FfqeH0"
            },
            {
                "id": "happy4",
                "name": "Good as Hell",
                "artist": "Lizzo",
                "album": "Cuz I Love You",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273e33c30e28365085952eb1128",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/3Yh9lZcWyKrK9GjbhuS0hT"
            },
            {
                "id": "happy5",
                "name": "Uptown Funk",
                "artist": "Mark Ronson ft. Bruno Mars",
                "album": "Uptown Special",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273e619b5476383889dbba224b8",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/32OlwWuMpZ6b0aN2RZOeMS"
            }
        ],
        "sad": [
            {
                "id": "sad1",
                "name": "Someone Like You",
                "artist": "Adele",
                "album": "21",
                "image_url": "https://i.scdn.co/image/ab67616d0000b2732118bf9b198b05a95ded6300",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/4kflIGfjdZJW4ot2ioixTB"
            },
            {
                "id": "sad2",
                "name": "Fix You",
                "artist": "Coldplay",
                "album": "X&Y",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273de0cd11d7b31c3bd1fd5983d",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/7LVHVU3tWfcxj5aiPFEW4Q"
            },
            {
                "id": "sad3",
                "name": "Hello",
                "artist": "Adele",
                "album": "25",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273e35b473c6846336b96a35925",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/4sPmO7WMQUAf45kwMOtONw"
            },
            {
                "id": "sad4",
                "name": "Skinny Love",
                "artist": "Bon Iver",
                "album": "For Emma, Forever Ago",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273e207c89effe1730fdf577932",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/0BhuO4S1yzHb417yTWKQT2"
            },
            {
                "id": "sad5",
                "name": "Tears in Heaven",
                "artist": "Eric Clapton",
                "album": "Rush (Music from the Motion Picture Soundtrack)",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273f5a00bdcd8bda92d9c1b6ca5",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/612VcBshQcy4mpB2utGc3H"
            }
        ],
        "angry": [
            {
                "id": "angry1",
                "name": "Break Stuff",
                "artist": "Limp Bizkit",
                "album": "Significant Other",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273c04a1f4026c5d629b6a0c710",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/5cZqsjJuSxcmlgcktjaLNO"
            },
            {
                "id": "angry2",
                "name": "Killing In The Name",
                "artist": "Rage Against The Machine",
                "album": "Rage Against The Machine",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273c8a11e48c91a982d086afc69",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/59WN2psjkt1tyaxjspN8fp"
            },
            {
                "id": "angry3",
                "name": "Bulls On Parade",
                "artist": "Rage Against The Machine",
                "album": "Evil Empire",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273e3e3b64cea45265469d4cafa",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/1aVgyDQukYk0LUJOKvGdQh"
            },
            {
                "id": "angry4",
                "name": "Last Resort",
                "artist": "Papa Roach",
                "album": "Infest",
                "image_url": "https://i.scdn.co/image/ab67616d0000b2736f7be9181d779e0e8c34f63a",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/0o7g4apWcIvt8VhYRGYjgd"
            },
            {
                "id": "angry5",
                "name": "Given Up",
                "artist": "Linkin Park",
                "album": "Minutes to Midnight",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273ded4afdd6b3a2f8fc57e8bd0",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/3qL6pIUVoYieuaHZJZfN4p"
            }
        ],
        "calm": [
            {
                "id": "calm1",
                "name": "Weightless",
                "artist": "Marconi Union",
                "album": "Weightless",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273e3424f7da9bffd6c6cdec1e4",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/4HI45IKz6DPq96I9P30utl"
            },
            {
                "id": "calm2",
                "name": "Clair de Lune",
                "artist": "Claude Debussy",
                "album": "Relaxing Classical",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273ca1ab9bafa3af8ef32cf8810",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/4OdS71RDlgxK6KSzQgEANJ"
            },
            {
                "id": "calm3",
                "name": "Experience",
                "artist": "Ludovico Einaudi",
                "album": "In A Time Lapse",
                "image_url": "https://i.scdn.co/image/ab67616d0000b27308f6df33eac677f0a8ee2258",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/1BncfTJAWxrsxyT9culBrj"
            },
            {
                "id": "calm4",
                "name": "Gymnopedie No. 1",
                "artist": "Erik Satie",
                "album": "Gymnopédies",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273728de04c4280f421c5afdda6",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/1I6oT797UrjUDdkuzOAIR3"
            },
            {
                "id": "calm5",
                "name": "Intro",
                "artist": "The xx",
                "album": "xx",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273be5b4ddd5806ea63f8aa3ef4",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/0fDG6v4QBGYpK7cFICQuis"
            }
        ],
        "energetic": [
            {
                "id": "energetic1",
                "name": "Eye of the Tiger",
                "artist": "Survivor",
                "album": "Eye of the Tiger",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273e8ddd32c41af1025272222c7",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/2KH16WveTQWT6KOG9Rg6e2"
            },
            {
                "id": "energetic2",
                "name": "Can't Hold Us",
                "artist": "Macklemore & Ryan Lewis",
                "album": "The Heist",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273883106c45e2e5e1d5186caa5",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/3bidbhpOYeV4knp8AIu8Xn"
            },
            {
                "id": "energetic3",
                "name": "Wake Me Up",
                "artist": "Avicii",
                "album": "True",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273c31d4b0853f7f5a23b38e2dd",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/0nJW01T7XtvILxQgC5J7Wh"
            },
            {
                "id": "energetic4",
                "name": "Stronger",
                "artist": "Kanye West",
                "album": "Graduation",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273e3f3de66770be1b3ded47056",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/4fzsfWzRhPawzqhX8Qt9F3"
            },
            {
                "id": "energetic5",
                "name": "All I Do Is Win",
                "artist": "DJ Khaled",
                "album": "Victory",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273942a0c9ac8f7ab8a5ab9a101",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/3Y3pdzh1g2R63LKWIBNblr"
            }
        ],
        "neutral": [
            {
                "id": "neutral1",
                "name": "Here Comes the Sun",
                "artist": "The Beatles",
                "album": "Abbey Road",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273dc30583ba717007b00cceb25",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/6dGnYIeXmHdcikdzNNDMm2"
            },
            {
                "id": "neutral2",
                "name": "Dreams",
                "artist": "Fleetwood Mac",
                "album": "Rumours",
                "image_url": "https://i.scdn.co/image/ab67616d0000b273e52a59a28efa4773dd2bfe1b",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/0ofHAoxe9vBkTCp2UQIavz"
            },
            {
                "id": "neutral3",
                "name": "Africa",
                "artist": "TOTO",
                "album": "Toto IV",
                "image_url": "https://i.scdn.co/image/ab67616d0000b2735752919c33697c001c8db419",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/2374M0fQpWi3dLnB54qaLX"
            },
            {
                "id": "neutral4",
                "name": "Hotel California",
                "artist": "Eagles",
                "album": "Hotel California",
                "image_url": "https://i.scdn.co/image/ab67616d0000b2738eaff1cf7982f95328028a4d",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/40riOy7x9W7GXjyGp4pjAv"
            },
            {
                "id": "neutral5",
                "name": "Imagine",
                "artist": "John Lennon",
                "album": "Imagine",
                "image_url": "https://i.scdn.co/image/ab67616d0000b2733c19c30050330476c61aea37",
                "preview_url": None,
                "external_url": "https://open.spotify.com/track/7pKfPomDEeI4TPT6EOYjn9"
            }
        ]
    }
    
    # Mapping of similar emotions to available mock data
    emotion_mapping = {
        "happy": "happy",
        "excited": "happy",
        "confident": "happy",
        "cheerful": "happy",
        
        "sad": "sad",
        "melancholic": "sad",
        "depressed": "sad",
        "gloomy": "sad",
        
        "angry": "angry",
        "irritated": "angry",
        "annoyed": "angry",
        "frustrated": "angry",
        
        "calm": "calm",
        "relaxed": "calm",
        "peaceful": "calm",
        "serene": "calm",
        
        "energetic": "energetic",
        "lively": "energetic",
        "dynamic": "energetic",
        "vigorous": "energetic",
        
        "neutral": "neutral",
        "balanced": "neutral",
        "indifferent": "neutral"
    }
    
    # Note about Spotify API restrictions
    print("""
NOTE: Spotify has restricted access to the Recommendations API for new applications 
since November 2023. This is why you're seeing mock data instead of real recommendations.
For more information, see: https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api
    """)
    
    # Return the appropriate mock data for the emotion, or neutral if not found
    mapped_emotion = emotion_mapping.get(emotion_type.lower(), "neutral")
    return mock_data.get(mapped_emotion, mock_data["neutral"])

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
        # Create Spotify client with OAuth to allow playlist creation
        sp = create_spotify_client()
        if not sp:
            return None
        
        # Create a new playlist
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=True,
            description=description or f"Playlist created based on mood or weather"
        )
        
        # Add tracks to the playlist
        if track_ids:
            sp.playlist_add_items(playlist["id"], track_ids)
        
        return {
            "id": playlist["id"],
            "name": playlist["name"],
            "url": playlist["external_urls"]["spotify"],
            "tracks_count": len(track_ids)
        }
    
    except Exception as e:
        print(f"Error creating playlist: {e}")
        return None

def get_current_user():
    """
    Get the current user's Spotify profile information.
    
    Returns:
        dict: User profile information including ID.
    """
    try:
        # Create Spotify client with OAuth for user info
        sp = create_spotify_client()
        if not sp:
            return None
        
        # Get user profile
        user = sp.current_user()
        return user
    
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return None

def search_track(query, limit=10):
    """
    Search for tracks on Spotify.
    
    Args:
        query (str): The search query.
        limit (int, optional): Maximum number of results to return. Defaults to 10.
        
    Returns:
        List[dict]: List of track results.
    """
    try:
        # Get Spotify client
        sp = get_spotify_client()
        if not sp:
            return []
        
        # Search for tracks
        results = sp.search(q=query, type='track', limit=limit)
        
        # Format results
        tracks = []
        for item in results['tracks']['items']:
            tracks.append({
                "id": item['id'],
                "name": item['name'],
                "artist": item['artists'][0]['name'] if item['artists'] else "Unknown Artist",
                "album": item['album']['name'] if item['album'] else "Unknown Album",
                "image_url": item['album']['images'][0]['url'] if item['album']['images'] else None,
                "preview_url": item['preview_url'],
                "external_url": item['external_urls']['spotify'] if 'external_urls' in item else None
            })
        
        return tracks
    
    except Exception as e:
        print(f"Error searching for tracks: {e}")
        return []

def search_tracks_by_mood(mood: str, limit: int = 20) -> List[dict]:
    """
    Search for tracks on Spotify based on mood using the Search endpoint with diversified results.
    
    This function maps moods to synonyms and related keywords, then makes multiple search queries
    to create a diverse set of results. It's designed to avoid returning tracks with all similar 
    titles by varying the search terms and combining multiple queries.
    
    Args:
        mood (str): The mood to search tracks for (e.g., "happy", "sad", "calm").
        limit (int, optional): Maximum number of tracks to return. Default is 20.
        
    Returns:
        List[dict]: List of exactly 20 tracks (or best effort if fewer are available), each containing:
            - id: Spotify track ID
            - name: Track name
            - artist: Artist name
            - album: Album name
            - image_url: URL to album cover
            - preview_url: URL to audio preview (if available)
            - external_url: URL to the track on Spotify
    """
    try:
        print(f"Searching for diverse tracks matching mood: {mood}")
        
        # Normalize the mood
        normalized_mood = mood.lower()
        
        # Get synonym lists for the given mood, or use the mood itself if no mapping exists
        mood_synonyms = mood_keywords.get(normalized_mood, [normalized_mood])
        
        # Get genre list for the given mood, or use a default set
        genre_list = genre_by_mood.get(normalized_mood, ["pop", "rock", "indie"])
        
        # Get Spotify client
        sp = get_spotify_client()
        if not sp:
            print("Failed to initialize Spotify client")
            return get_mock_recommendations(normalized_mood)
        
        # Get a fresh token using the existing auth manager
        token = sp._auth_manager.get_access_token(as_dict=False)
        
        # Set up headers with the token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Shuffling the synonyms and genres for more variety
        random.shuffle(mood_synonyms)
        random.shuffle(genre_list)
        
        # Initialize results storage
        all_tracks = []
        
        # Used to track unique tracks to avoid duplicates
        track_ids_seen = set()
        
        # We'll try different combinations of synonyms and genres to get diverse results
        # First, make individual queries for each synonym with a random genre
        for keyword in mood_synonyms[:3]:  # Limit to first 3 synonyms to avoid too many API calls
            # Randomly select a genre for this keyword
            genre = random.choice(genre_list)
            
            # Construct query with additional operators for more targeted results
            query = f"{keyword} genre:{genre}"
            
            # We'll try a different approach for each query to maximize diversity
            # Sometimes add NOT operators to filter out tracks with the mood directly in the title
            if random.random() > 0.5:
                query += f" NOT {normalized_mood}"
                
            print(f"Making search query: {query}")
            
            # Build query parameters
            params = {
                "q": query,
                "type": "track",
                "limit": min(50, limit),  # Spotify accepts max 50 items for search
                "market": "US"  # Ensure we get playable tracks
            }
            
            # Make the direct API request
            response = requests.get(
                "https://api.spotify.com/v1/search",
                headers=headers,
                params=params
            )
            
            # Process results if successful
            if response.status_code == 200:
                results = response.json()
                
                # Check if we got tracks
                if results and "tracks" in results and "items" in results["tracks"]:
                    items = results["tracks"]["items"]
                    print(f"Found {len(items)} tracks for keyword '{keyword}'")
                    
                    # Process the tracks
                    for item in items:
                        track_id = item["id"]
                        
                        # Skip if we've already seen this track
                        if track_id in track_ids_seen:
                            continue
                            
                        track_ids_seen.add(track_id)
                        
                        # Extract track information
                        track = {
                            "id": track_id,
                            "name": item["name"],
                            "artist": item["artists"][0]["name"] if item.get("artists") else "Unknown Artist",
                            "album": item.get("album", {}).get("name", "Unknown Album"),
                            "image_url": item.get("album", {}).get("images", [{}])[0].get("url") if item.get("album", {}).get("images") else None,
                            "preview_url": item.get("preview_url"),
                            "external_url": item.get("external_urls", {}).get("spotify", "https://spotify.com")
                        }
                        all_tracks.append(track)
                        
                        # If we've collected enough unique tracks, we can stop
                        if len(all_tracks) >= limit:
                            break
            
            # If we've collected enough unique tracks, we can stop
            if len(all_tracks) >= limit:
                break
        
        # If we still need more tracks, try artist-specific search for popular artists in the genre
        if len(all_tracks) < limit:
            popular_artists_by_genre = {
                "pop": ["Taylor Swift", "Ed Sheeran", "Ariana Grande", "Justin Bieber", "Dua Lipa"],
                "rock": ["Imagine Dragons", "Twenty One Pilots", "Coldplay", "The Killers", "Queen"],
                "indie": ["Arctic Monkeys", "The 1975", "Tame Impala", "Vampire Weekend", "Florence + The Machine"],
                "hip-hop": ["Drake", "Kendrick Lamar", "Post Malone", "J. Cole", "Travis Scott"],
                "r&b": ["The Weeknd", "SZA", "H.E.R.", "Frank Ocean", "Daniel Caesar"],
                "electronic": ["Calvin Harris", "Marshmello", "Daft Punk", "Kygo", "Avicii"],
                "dance": ["Dua Lipa", "Lady Gaga", "Calvin Harris", "David Guetta", "Swedish House Mafia"],
                "metal": ["Metallica", "Slipknot", "System of a Down", "Rammstein", "Iron Maiden"],
                "classical": ["Ludovico Einaudi", "Hans Zimmer", "Max Richter", "Philip Glass", "Nils Frahm"],
                "jazz": ["Kamasi Washington", "Robert Glasper", "Norah Jones", "Gregory Porter", "Esperanza Spalding"]
            }
            
            # Select a suitable genre based on the mood
            mood_genre = random.choice(genre_list)
            relevant_genre = next((genre for genre in popular_artists_by_genre.keys() if genre in mood_genre), "pop")
            
            # Get artists for the selected genre
            artists = popular_artists_by_genre.get(relevant_genre, popular_artists_by_genre["pop"])
            random.shuffle(artists)
            
            # Try artist-specific search
            for artist in artists[:2]:  # Limit to 2 artists
                keyword = random.choice(mood_synonyms)
                query = f"{keyword} artist:{artist}"
                
                print(f"Making artist-specific search: {query}")
                
                params = {
                    "q": query,
                    "type": "track",
                    "limit": min(50, limit - len(all_tracks)),
                    "market": "US"
                }
                
                response = requests.get(
                    "https://api.spotify.com/v1/search",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    if results and "tracks" in results and "items" in results["tracks"]:
                        items = results["tracks"]["items"]
                        print(f"Found {len(items)} tracks for artist '{artist}'")
                        
                        for item in items:
                            track_id = item["id"]
                            
                            if track_id in track_ids_seen:
                                continue
                                
                            track_ids_seen.add(track_id)
                            
                            track = {
                                "id": track_id,
                                "name": item["name"],
                                "artist": item["artists"][0]["name"] if item.get("artists") else "Unknown Artist",
                                "album": item.get("album", {}).get("name", "Unknown Album"),
                                "image_url": item.get("album", {}).get("images", [{}])[0].get("url") if item.get("album", {}).get("images") else None,
                                "preview_url": item.get("preview_url"),
                                "external_url": item.get("external_urls", {}).get("spotify", "https://spotify.com")
                            }
                            all_tracks.append(track)
                            
                            if len(all_tracks) >= limit:
                                break
                                
                # If we've collected enough unique tracks, we can stop
                if len(all_tracks) >= limit:
                    break
        
        # If we still need more tracks, try a year range filter
        years = ["2020", "2019", "2018", "2021", "2022", "2023"]
        if len(all_tracks) < limit:
            random.shuffle(years)
            keyword = random.choice(mood_synonyms)
            year = random.choice(years)
            
            query = f"{keyword} year:{year}"
            print(f"Making year-specific search: {query}")
            
            params = {
                "q": query,
                "type": "track",
                "limit": min(50, limit - len(all_tracks)),
                "market": "US"
            }
            
            response = requests.get(
                "https://api.spotify.com/v1/search",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                results = response.json()
                
                if results and "tracks" in results and "items" in results["tracks"]:
                    items = results["tracks"]["items"]
                    print(f"Found {len(items)} tracks for year '{year}'")
                    
                    for item in items:
                        track_id = item["id"]
                        
                        if track_id in track_ids_seen:
                            continue
                            
                        track_ids_seen.add(track_id)
                        
                        track = {
                            "id": track_id,
                            "name": item["name"],
                            "artist": item["artists"][0]["name"] if item.get("artists") else "Unknown Artist",
                            "album": item.get("album", {}).get("name", "Unknown Album"),
                            "image_url": item.get("album", {}).get("images", [{}])[0].get("url") if item.get("album", {}).get("images") else None,
                            "preview_url": item.get("preview_url"),
                            "external_url": item.get("external_urls", {}).get("spotify", "https://spotify.com")
                        }
                        all_tracks.append(track)
                        
                        if len(all_tracks) >= limit:
                            break
        
        # As a last resort, if we still don't have enough tracks, just use the mood directly
        if len(all_tracks) < limit:
            print(f"Still need more tracks. Searching directly with mood: {normalized_mood}")
            
            params = {
                "q": normalized_mood,
                "type": "track",
                "limit": min(50, limit - len(all_tracks)),
                "market": "US"
            }
            
            response = requests.get(
                "https://api.spotify.com/v1/search",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                results = response.json()
                
                if results and "tracks" in results and "items" in results["tracks"]:
                    items = results["tracks"]["items"]
                    print(f"Found {len(items)} tracks for direct mood search")
                    
                    for item in items:
                        track_id = item["id"]
                        
                        if track_id in track_ids_seen:
                            continue
                            
                        track_ids_seen.add(track_id)
                        
                        track = {
                            "id": track_id,
                            "name": item["name"],
                            "artist": item["artists"][0]["name"] if item.get("artists") else "Unknown Artist",
                            "album": item.get("album", {}).get("name", "Unknown Album"),
                            "image_url": item.get("album", {}).get("images", [{}])[0].get("url") if item.get("album", {}).get("images") else None,
                            "preview_url": item.get("preview_url"),
                            "external_url": item.get("external_urls", {}).get("spotify", "https://spotify.com")
                        }
                        all_tracks.append(track)
                        
                        if len(all_tracks) >= limit:
                            break
        
        # Summarize the results
        if all_tracks:
            print(f"Successfully found {len(all_tracks)} unique tracks for mood: {normalized_mood}")
            
            # If we have more tracks than requested, randomly select the exact number
            if len(all_tracks) > limit:
                all_tracks = random.sample(all_tracks, limit)
                print(f"Randomly selected {limit} tracks from the pool")
                
            # If we have fewer tracks than requested, fill with mock data
            elif len(all_tracks) < limit:
                needed = limit - len(all_tracks)
                print(f"Found only {len(all_tracks)} tracks, adding {needed} mock tracks to reach {limit}")
                
                mock_tracks = get_mock_recommendations(normalized_mood)
                
                # Add mock tracks to reach the limit, avoiding duplicates by track name
                track_names_seen = {track["name"] for track in all_tracks}
                
                for mock_track in mock_tracks:
                    if mock_track["name"] not in track_names_seen and len(all_tracks) < limit:
                        all_tracks.append(mock_track)
                        track_names_seen.add(mock_track["name"])
            
            return all_tracks
        
        # If we couldn't find any tracks, fall back to mock data
        print(f"All search attempts failed. Returning mock data for mood: {normalized_mood}")
        mock_data = get_mock_recommendations(normalized_mood)
        
        # Ensure we return exactly 20 tracks
        if len(mock_data) >= limit:
            return mock_data[:limit]
        else:
            # Repeat mock data if needed to reach the limit
            return [mock_data[i % len(mock_data)] for i in range(limit)]
        
    except Exception as e:
        print(f"Error searching for tracks by mood: {e}")
        # Return mock data on error, ensuring exactly 20 tracks
        mock_data = get_mock_recommendations(mood)
        if len(mock_data) >= limit:
            return mock_data[:limit]
        else:
            # Repeat mock data if needed to reach the limit
            return [mock_data[i % len(mock_data)] for i in range(limit)]

def get_track_info(track_id):
    """
    Get detailed information about a specific track.
    
    Args:
        track_id (str): The Spotify track ID.
        
    Returns:
        dict: Track information.
    """
    try:
        # Get Spotify client
        sp = get_spotify_client()
        if not sp:
            return None
        
        # Get track information
        track = sp.track(track_id)
        
        # Format track info
        return {
            "id": track["id"],
            "name": track["name"],
            "artist": track["artists"][0]["name"] if track["artists"] else "Unknown Artist",
            "album": track["album"]["name"] if track["album"] else "Unknown Album",
            "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "preview_url": track["preview_url"],
            "external_url": track["external_urls"]["spotify"] if "external_urls" in track else None,
            "popularity": track.get("popularity", 0),
            "duration_ms": track.get("duration_ms", 0)
        }
    
    except Exception as e:
        print(f"Error getting track info: {e}")
        return None

def generate_playlist_from_tracks(user_id, playlist_name, tracks, description=None):
    """
    Create a playlist from a list of track dictionaries.
    
    Args:
        user_id (str): The user's Spotify ID.
        playlist_name (str): Name for the new playlist.
        tracks (List[dict]): List of track dictionaries with 'id' field.
        description (str, optional): Description for the playlist.
        
    Returns:
        dict: Playlist information including ID and URL.
    """
    try:
        # Extract track IDs
        track_ids = [track["id"] for track in tracks if track.get("id") and not track["id"].startswith("mock")]
        
        # Create playlist
        if track_ids:
            return create_playlist(user_id, playlist_name, track_ids, description)
        else:
            print("No valid track IDs found for playlist creation")
            return None
    
    except Exception as e:
        print(f"Error generating playlist from tracks: {e}")
        return None

if __name__ == "__main__":
    import sys
    import textwrap
    
    # Display important info about Spotify API restrictions
    print(textwrap.dedent("""
    -------------------------------------------------------------------------
    IMPORTANT: Spotify API Restrictions
    -------------------------------------------------------------------------
    
    As of November 2023, Spotify has restricted access to several API endpoints
    for new applications, including the Recommendations endpoint. This means
    that new applications can no longer access these endpoints, resulting in
    404 errors.
    
    Affected endpoints include:
    1. Recommendations
    2. Audio Features
    3. Audio Analysis
    4. And several others
    
    For more information, see:
    https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api
    
    We're now using the Search API as an alternative to find tracks by mood!
    -------------------------------------------------------------------------
    """))
    
    # Run the authentication test
    print("Running Spotify API authentication test...")
    auth_success = test_spotify_authentication()
    
    if not auth_success:
        print("\n⚠️ Authentication test failed. Search functionality may not work correctly.")
    else:
        print("\n✓ Authentication test passed. Testing mood-based search...")
        
        # Test the search_tracks_by_mood function
        print("\n========= TESTING MOOD-BASED TRACK SEARCH =========\n")
        
        # Test with "happy" mood
        mood_to_test = "happy"
        print(f"Testing search_tracks_by_mood with mood: {mood_to_test}")
        
        tracks = search_tracks_by_mood(mood_to_test)
        
        print(f"\nFound {len(tracks)} tracks for mood '{mood_to_test}':")
        print("-" * 80)
        
        for i, track in enumerate(tracks, 1):
            print(f"{i}. {track['name']} by {track['artist']}")
        
        print("\n========= END OF TEST =========\n")
    
    # Let the user know about usage
    print("\n-------------------------------------------------------------------------")
    print("HOW TO USE THE MOOD-BASED SEARCH:")
    print("-------------------------------------------------------------------------")
    print("1. Import the function:")
    print("   from spotify_utils.spotify_api import search_tracks_by_mood")
    print()
    print("2. Call it with a mood string:")
    print("   tracks = search_tracks_by_mood('happy', limit=10)")
    print()
    print("3. Process the returned tracks:")
    print("   for track in tracks:")
    print("       print(f\"{track['name']} by {track['artist']}\")")
    print()
    print("Available moods: happy, sad, angry, calm, energetic, anxious, relaxed,")
    print("                nostalgic, romantic, confident, fearful, surprised, neutral")
    print("-------------------------------------------------------------------------") 
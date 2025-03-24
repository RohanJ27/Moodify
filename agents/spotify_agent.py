import os
import sys
import uuid
from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from pydantic import BaseModel, Field
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from spotify_utils.spotify_api import get_recommendations, create_playlist, get_current_user

# Load environment variables
load_dotenv()

# Create the agent in a function to avoid import-time initialization
def create_spotify_agent():
    return Agent(
        name="spotify_agent",
        seed=os.getenv("SPOTIFY_AGENT_SEED", "spotify_agent_seed"),
    )

# Create a lazy-loaded agent instance
spotify_agent = None

class SpotifyAgent:
    def __init__(self):
        """
        Initialize SpotifyAgent to interact with the Spotify API.
        """
        pass

    def get_recommendations(self, emotion, limit=10):
        """
        Get track recommendations based on the given emotion.
        
        Args:
            emotion (str): The emotion to base recommendations on.
            limit (int): Number of tracks to recommend.
            
        Returns:
            list: List of recommended tracks.
        """
        try:
            # Use Spotify API to get recommendations
            tracks = get_recommendations(emotion, limit)
            return tracks
        
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []
    
    def create_playlist(self, user_id, playlist_name, track_ids, description=None):
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
            # Create playlist using Spotify API
            playlist = create_playlist(user_id, playlist_name, track_ids, description)
            return playlist
        
        except Exception as e:
            print(f"Error creating playlist: {e}")
            return None

# Create a Protocol for Spotify operations
spotify_protocol = Protocol("spotify")

# Define message models for Spotify operations
class RecommendationsRequest(BaseModel):
    operation: str
    emotion: str = None
    limit: int = 10
    requester: str = None

class PlaylistRequest(BaseModel):
    operation: str
    user_id: str = None
    playlist_name: str = None
    track_ids: list = None
    description: str = None
    emotion: str = None
    requester: str = None

@spotify_protocol.on_message(model=RecommendationsRequest)
async def handle_recommendations_request(ctx: Context, sender: str, msg: RecommendationsRequest):
    """
    Handle recommendation requests.
    """
    if msg.operation == "get_recommendations":
        emotion = msg.emotion
        limit = msg.limit
        requester = msg.requester or sender
        
        if not emotion:
            await ctx.send(requester, {"error": "Emotion is required for recommendations"})
            return
        
        spotify_agent_instance = SpotifyAgent()
        tracks = spotify_agent_instance.get_recommendations(emotion, limit)
        
        # Send the recommendations to the requester
        await ctx.send(requester, {
            "status": "success",
            "tracks": tracks,
            "emotion": emotion
        })

@spotify_protocol.on_message(model=PlaylistRequest)
async def handle_playlist_request(ctx: Context, sender: str, msg: PlaylistRequest):
    """
    Handle playlist creation requests.
    """
    if msg.operation == "create_playlist":
        user_id = msg.user_id
        playlist_name = msg.playlist_name or f"Playlist based on {msg.emotion or 'mood'}"
        track_ids = msg.track_ids or []
        description = msg.description or f"Created by Mood & Weather Playlist Creator"
        requester = msg.requester or sender
        
        if not user_id:
            await ctx.send(requester, {"error": "User ID is required for playlist creation"})
            return
        
        if not track_ids:
            await ctx.send(requester, {"error": "Track IDs are required for playlist creation"})
            return
        
        spotify_agent_instance = SpotifyAgent()
        playlist = spotify_agent_instance.create_playlist(user_id, playlist_name, track_ids, description)
        
        # Send the playlist information to the requester
        if playlist:
            await ctx.send(requester, {
                "status": "success",
                "playlist": playlist
            })
        else:
            await ctx.send(requester, {
                "status": "error",
                "message": "Failed to create playlist"
            })

# Get the agent and include the protocol only when needed
def get_spotify_agent():
    global spotify_agent
    if spotify_agent is None:
        spotify_agent = create_spotify_agent()
        spotify_agent.include(spotify_protocol)
    return spotify_agent 
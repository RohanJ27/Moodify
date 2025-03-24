import os
import sys
import json

# Add paths needed for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, 'spotify_utils'))

# Import directly from the spotify_api module
from spotify_utils.spotify_api import get_spotify_client, get_current_user, create_playlist


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
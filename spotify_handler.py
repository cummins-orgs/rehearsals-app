import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
import requests

class SpotifyPodcastHandler:
    def __init__(self, show_name="rehearsals"):
        load_dotenv()
        
        # Basic validation of required environment variables
        required_vars = ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_SHOW_ID"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        self.show_name = show_name
        self.show_id = os.getenv("SPOTIFY_SHOW_ID")
        
        try:
            # Initialize Spotify client with client credentials flow
            auth_manager = SpotifyClientCredentials()
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test the connection
            self.sp.show(self.show_id)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Spotify client: {str(e)}")
        
        # API endpoint for episode upload (not part of spotipy)
        self.base_url = "https://api.spotify.com/v1/shows"

    def upload_episode(self, audio_data: bytes, title: str, description: str) -> Optional[str]:
        """
        Upload a new episode to the Spotify podcast
        
        Args:
            audio_data: Binary audio data
            title: Episode title
            description: Episode description
            
        Returns:
            str: Episode ID if successful, None if failed
        """
        try:
            # Get the current access token from spotipy
            token = self.sp.auth_manager.get_access_token()
            
            # Endpoint for episode upload
            upload_url = f"{self.base_url}/{self.show_id}/episodes"
            
            # Headers using the token from spotipy
            headers = {
                "Authorization": f"Bearer {token['access_token']}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Prepare episode metadata
            episode_data = {
                "name": title,
                "description": description,
                "language": "en",
                "audio": audio_data,
                "publish_date": datetime.now().isoformat(),
            }
            
            # Make the upload request
            response = requests.post(
                upload_url,
                headers=headers,
                data=episode_data
            )
            
            if response.status_code == 201:
                return response.json().get('id')
            else:
                print(f"Upload failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error uploading episode: {str(e)}")
            return None
    
    def get_episode_url(self, episode_id: str) -> Optional[str]:
        """Get the Spotify URL for an episode"""
        if episode_id:
            return f"https://open.spotify.com/episode/{episode_id}"
        return None
    
    def get_show_details(self) -> dict:
        """Get details about the podcast show"""
        try:
            return self.sp.show(self.show_id)
        except Exception as e:
            print(f"Error getting show details: {str(e)}")
            return {}
    
    def get_episodes(self, limit: int = 50) -> list:
        """Get list of episodes in the show"""
        try:
            results = self.sp.show_episodes(self.show_id, limit=limit)
            return results.get('items', [])
        except Exception as e:
            print(f"Error getting episodes: {str(e)}")
            return []
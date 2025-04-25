from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_video_title(video_id):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY is not set in environment variables")

    res = requests.get(f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}")
    data = res.json()

    if "items" not in data or len(data["items"]) == 0:
        raise ValueError(f"Could not find video with ID {video_id}")

    title = data["items"][0]["snippet"]["title"]
    return title

def get_video_data(url):
    video_id = get_video_id(url)
    if not video_id:
        raise ValueError("Could not extract video ID from URL")

    # Default empty transcript
    transcript = "[No transcript available]"
    title = get_video_title(video_id)  # Always try to get the title

    ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username="qpywvtbt",
        proxy_password="1syhdy3pmfer",
        )
    )

    try:
        # Try English first
        transcript_list = ytt_api.get_transcript(video_id, languages=['en'])
        transcript = " ".join([entry["text"] for entry in transcript_list])
    except Exception:
        try:
            # Fallback to any available language
            transcript_list = ytt_api.get_transcript(video_id)
            transcript = " ".join([entry["text"] for entry in transcript_list])
        except Exception:
            # If no transcript exists, keep default "[No transcript available]"
            pass  # No error, just proceed with default

    return title, transcript

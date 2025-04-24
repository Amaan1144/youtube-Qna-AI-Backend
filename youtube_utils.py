from youtube_transcript_api import YouTubeTranscriptApi
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
        raise ValueError("Invalid YouTube URL")

    try:
        # Try English first
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    except Exception as e:
        # Log the exact error for debugging
        print(f"Transcript fetch failed (English): {str(e)}")
        try:
            # Fallback to any language
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            # Critical: Don't proceed if no transcript exists
            raise ValueError(f"No transcript available for video {video_id}. Original error: {str(e)}")

    transcript = " ".join([entry["text"] for entry in transcript_list])
    title = get_video_title(video_id)  # Ensure this works on Render too
    return title, transcript

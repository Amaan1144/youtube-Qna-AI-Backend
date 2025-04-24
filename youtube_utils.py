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

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_video_data(url):
    video_id = get_video_id(url)
    logger.info(f"Fetching data for video ID: {video_id}")
    
    try:
        title = get_video_title(video_id)
        logger.info(f"Title fetched: {title}")
        
        # Try English transcript first, then any language
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        except:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)  # Fallback to any language
            
        transcript = " ".join([entry["text"] for entry in transcript_list])
        return title, transcript
        
    except Exception as e:
        logger.error(f"No transcript available: {str(e)}")
        return title, None  # Return title + None for transcript

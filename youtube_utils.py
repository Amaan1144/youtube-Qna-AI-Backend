from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._api import TranscriptList
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

PROXIES = [
    {
        "http": "http://181.30.67.132:3663",
        "https": "http://3.136.29.104:80",
    },
    {
        "http": "http://13.59.156.167:3128",
        "https": "http://190.52.100.170:999",
    },
]

def get_video_data(url):
    video_id = get_video_id(url)
    if not video_id:
        raise ValueError("Could not extract video ID from URL")

    title = get_video_title(video_id)
    transcript = "[No transcript available]"

    for proxy in PROXIES:
        try:
            # Monkey patch the requests session inside the API
            session = requests.Session()
            session.proxies.update(proxy)
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            })
            TranscriptList._TranscriptApi__session = session

            # Try English transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            transcript = " ".join([entry["text"] for entry in transcript_list])
            break  # Exit the loop if successful

        except Exception as e:
            try:
                # Try any available language
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                transcript = " ".join([entry["text"] for entry in transcript_list])
                break
            except Exception:
                continue  # Try next proxy

    return title, transcript

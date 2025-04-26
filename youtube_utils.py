import os
import re
import requests
from dotenv import load_dotenv
import speech_recognition as sr
from pytubefix import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

load_dotenv()

def get_video_id(url):
    """Extract YouTube video ID from URL"""
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_video_title(video_id):
    """Get video title using YouTube API"""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return "Unknown Title"
    
    res = requests.get(f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}")
    data = res.json()
    
    if "items" not in data or len(data["items"]) == 0:
        return "Unknown Title"
    
    return data["items"][0]["snippet"]["title"]

def get_transcript_from_api(video_id):
    """Try to get transcript using YouTube Transcript API in the video's original language"""
    # Setup proxy if credentials are available
    proxy_config = None
    proxy_username = os.getenv("PROXY_USERNAME")
    proxy_password = os.getenv("PROXY_PASSWORD")
    
    if proxy_username and proxy_password:
        proxy_config = WebshareProxyConfig(
            proxy_username=proxy_username,
            proxy_password=proxy_password
        )
    
    try:
        # First try to get the transcript without specifying language (gets original language)
        transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxy_config)
        return " ".join([entry["text"] for entry in transcript])
                
    except Exception as e:
        # Try common languages as fallback
        for lang in ["en", "hi", "pa", "es", "fr", "de", "ja", "ru", "pt"]:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang], proxies=proxy_config)
                print(f"Found transcript in {lang}")
                return " ".join([entry["text"] for entry in transcript])
            except:
                continue
        return None

def transcribe_audio(audio_file):
    """Transcribe audio file using Google Speech Recognition"""
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = r.record(source)
    
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service: {e}")
        return None

def get_transcript_from_audio(url):
    """Download audio and transcribe it"""
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        if not audio_stream:
            return None
        
        audio_file = audio_stream.download(output_path=".")
        
        transcript = transcribe_audio(audio_file)
        
        # Clean up downloaded audio file
        os.remove(audio_file)
        
        return transcript
    except Exception as e:
        return None

def get_video_data(url):
    """Main function to get video transcript using available methods"""
    video_id = get_video_id(url)
    if not video_id:
        return "Error: Could not extract video ID from URL", None
    
    # Get video title
    title = get_video_title(video_id)
    
    # Try getting transcript from API first
    transcript = get_transcript_from_api(video_id)
    
    # If API method fails, try audio transcription
    if not transcript:
        transcript = get_transcript_from_audio(url)
    
    if not transcript:
        transcript = "[No transcript available]"
    
    return title, transcript
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
    import yt_dlp
    
    video_id = get_video_id(url)
    if not video_id:
        raise ValueError("Could not extract video ID from URL")
    
    # Get title and transcript using yt-dlp
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', f"Unknown Video ({video_id})")
        
        # Try to get the transcript from the subtitles
        transcript = "[No transcript available]"
        if 'subtitles' in info and info['subtitles']:
            # Process available subtitles
            for lang, sub_info in info['subtitles'].items():
                for sub_format in sub_info:
                    if sub_format.get('ext') == 'vtt':
                        transcript_url = sub_format.get('url')
                        if transcript_url:
                            response = requests.get(transcript_url)
                            if response.status_code == 200:
                                # Parse VTT content to extract text
                                transcript = parse_vtt_content(response.text)
                                break
        
        # If no subtitle found, try automatic captions
        if transcript == "[No transcript available]" and 'automatic_captions' in info:
            for lang, auto_caps in info['automatic_captions'].items():
                if lang.startswith('en'):  # Prioritize English
                    for cap_format in auto_caps:
                        if cap_format.get('ext') == 'vtt':
                            transcript_url = cap_format.get('url')
                            if transcript_url:
                                response = requests.get(transcript_url)
                                if response.status_code == 200:
                                    # Parse VTT content to extract text
                                    transcript = parse_vtt_content(response.text)
                                    break
    
    return title, transcript

def parse_vtt_content(vtt_content):
    """Extract plain text from VTT subtitle content"""
    import re
    
    # Remove header lines
    content_lines = vtt_content.split('\n')
    content_lines = [line for line in content_lines if not re.match(r'^(WEBVTT|Kind:|Language:|00:)', line)]
    
    # Extract text content, ignoring timestamps and other metadata
    text_lines = []
    for line in content_lines:
        if line.strip() and not re.match(r'^[0-9:.>-]', line):
            text_lines.append(line.strip())
    
    return ' '.join(text_lines)

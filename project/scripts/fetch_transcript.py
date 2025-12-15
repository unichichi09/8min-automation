
import sys
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

def get_video_id(url):
    """Extracts video ID from YouTube URL."""
    # Short URL
    match = re.search(r"youtu\.be\/([a-zA-Z0-9_-]+)", url)
    if match: return match.group(1)
    
    # Standard URL
    match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
    if match: return match.group(1)
    
    return None

def fetch_transcript(url, output_file=None):
    video_id = get_video_id(url)
    if not video_id:
        print("Error: Could not extract video ID from URL.")
        return None

    print(f"Fetching transcript for Video ID: {video_id}...")
    
    try:
        # Try Japanese first, then English, then auto-generated
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja', 'en', 'en-US'])
        
        formatter = TextFormatter()
        text = formatter.format_transcript(transcript)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Transcript saved to {output_file}")
            
        return text
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_transcript.py <youtube_url> [output_file]")
        sys.exit(1)
        
    url = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "transcript.txt"
    
    fetch_transcript(url, output)

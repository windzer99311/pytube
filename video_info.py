# video_info.py - YouTube video information extraction module
import streamlit as st
from pytubefix import YouTube
import time

# Function to format file size
def format_size(bytes_size):
    """Convert bytes to human-readable format"""
    if bytes_size is None:
        return "Unknown size"

    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} GB"


# Function to get video details
@st.cache_data(ttl=3600, show_spinner=False)
def get_video_info(url):
    """Extract video information from YouTube URL"""
    try:
        yt = YouTube(url)

        # Get basic video info
        title = yt.title
        thumbnail = yt.thumbnail_url
        duration = time.strftime('%H:%M:%S', time.gmtime(yt.length))

        # Get available video streams
        video_streams = {}
        for stream in yt.streams.filter(progressive=False):
            if stream.resolution:
                res = stream.resolution
                fps = stream.fps
                size_bytes = stream.filesize

                # Get the best quality stream for each resolution
                if res not in video_streams or video_streams[res]['fps'] < fps:
                    video_streams[res] = {
                        'fps': fps,
                        'size': format_size(size_bytes),
                        'size_bytes': size_bytes,
                        'stream': stream
                    }

        # Sort by resolution (highest first)
        sorted_streams = sorted(video_streams.items(),
                                key=lambda x: int(x[0][:-1]) if x[0][:-1].isdigit() else 0,
                                reverse=True)

        # Always get the first audio stream with lowest bitrate
        audio_stream = yt.streams.filter(only_audio=True).order_by('bitrate').asc().first()

        return {
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'video_streams': sorted_streams,
            'audio_stream': audio_stream,
            'yt': yt
        }
    except Exception as e:
        st.error(f"Error retrieving video information: {str(e)}")
        return None

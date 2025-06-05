# YouTube Downloader - Streamlit GUI with modular architecture
import streamlit as st
import os
import sys
import re
import time

# Add current directory to path to help with imports
sys.path.append(os.getcwd())

# Import from modular components
from video_info import get_video_info, format_size
import update_download
from merger import start_merg

st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎬",
    layout="centered"
)

# Create a persistent session state to track if a file is ready for download
if 'file_ready_for_download' not in st.session_state:
    st.session_state.file_ready_for_download = False
    st.session_state.download_file_path = None
    st.session_state.download_file_name = None
    st.session_state.video_file_path = None
    st.session_state.audio_file_path = None
    st.session_state.file_downloaded = False


# Function to delete the server-side files after download
def delete_server_files():
    """Delete downloaded files from the server after client has downloaded them"""
    files_to_delete = [
        st.session_state.download_file_path,
        st.session_state.video_file_path,
        st.session_state.audio_file_path
    ]

    for file_path in files_to_delete:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {str(e)}")

    # Reset session state
    st.session_state.file_ready_for_download = False
    st.session_state.download_file_path = None
    st.session_state.download_file_name = None
    st.session_state.video_file_path = None
    st.session_state.audio_file_path = None
    st.session_state.file_downloaded = True  # Mark as downloaded, the page will refresh on next interaction


# Function to download video using modular approach
def download_with_modular_approach(video_url, audio_url, title, threads=32):
    """Use update_download.start() to download the video with direct function calls"""
    try:
        # Create a safe filename from the title
        safe_title = "".join([c if c.isalnum() or c in [' ', '.', '_', '-'] else '_' for c in title])
        safe_title = safe_title.strip().replace(' ', '_')

        # Set output filenames based on the title
        video_output = f"{safe_title}.mp4"
        audio_output = f"{safe_title}.m4a"

        # Create progress placeholder for real-time updates
        progress_placeholder = st.empty()

        # Initialize progress tracking variables
        last_video_progress = 0
        last_audio_progress = 0
        video_speed = "0 B/s"
        audio_speed = "0 B/s"
        combined_progress = 0
        status_text = "Preparing download..."

        # Display initial progress
        with progress_placeholder.container():
            st.write("Download Progress:")
            st.progress(0)
            st.write(status_text)

        # Call update_download.start() directly with parameters
        success = update_download.start(
            video_stream=video_url,
            audio_stream=audio_url,
            thread=threads,
            video_file=video_output,
            audio_file=audio_output
        )

        if success:
            # Update progress to 100% on completion
            with progress_placeholder.container():
                st.write("Download Progress:")
                st.progress(1.0)
                st.write("Download completed! Processing final file...")

            # Use merger to combine video and audio
            video_path = os.path.abspath(video_output)
            audio_path = os.path.abspath(audio_output)
            
            # The merger will create a file with "_video" suffix
            merger_success = start_merg(video_path, audio_path)
            
            if merger_success:
                # Calculate the final merged file path
                final_path = os.path.abspath(
                    f"{os.path.splitext(video_output)[0]}_video{os.path.splitext(video_output)[1]}"
                )
                file_name = os.path.basename(final_path)

                # Set up the session state for auto-download and file cleanup
                st.session_state.file_ready_for_download = True
                st.session_state.download_file_path = final_path
                st.session_state.download_file_name = file_name
                st.session_state.video_file_path = video_path
                st.session_state.audio_file_path = audio_path

                # Success message
                st.success("✅ Download completed! Video will begin downloading automatically.")

                # Function to mark download as complete and trigger cleanup
                def on_download_complete():
                    st.session_state.file_downloaded = True
                    delete_server_files()

                # Auto-download file to the browser
                if os.path.exists(final_path):
                    with open(final_path, "rb") as file:
                        download_btn = st.download_button(
                            label=f"⬇️ DOWNLOAD VIDEO TO YOUR DEVICE",
                            data=file,
                            file_name=file_name,
                            mime="video/mp4",
                            key="auto_download_btn",
                            use_container_width=True,
                            help="Click to download the video if it doesn't start automatically",
                            on_click=on_download_complete
                        )

                return True
            else:
                st.error("Video merging failed. Please try again.")
                return False
        else:
            st.error("Download failed. Please check your connection and try again.")
            return False

    except Exception as e:
        st.error(f"Error during download: {str(e)}")
        return False


# Main app UI
st.title("YouTube Downloader")
st.markdown("Enter a YouTube URL to download the video")

# Check if there's a file ready for auto-download from previous run
if st.session_state.file_ready_for_download and st.session_state.download_file_path and os.path.exists(
        st.session_state.download_file_path):
    auto_download_container = st.container()
    with auto_download_container:
        file_path = st.session_state.download_file_path
        file_name = st.session_state.download_file_name

        st.success("✅ Your video is ready! Downloading now...")

        # Create a function to trigger cleanup after download
        def on_persistent_download_complete():
            st.session_state.file_downloaded = True
            delete_server_files()

        with open(file_path, "rb") as file:
            st.download_button(
                label=f"⬇️ DOWNLOAD VIDEO TO YOUR DEVICE",
                data=file,
                file_name=file_name,
                mime="video/mp4",
                key="persistent_download_btn",
                use_container_width=True,
                on_click=on_persistent_download_complete
            )

# URL input
url = st.text_input("YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")

if url:
    # Validate URL format
    if not ("youtube.com/watch" in url or "youtu.be/" in url):
        st.error("Please enter a valid YouTube URL")
    else:
        with st.spinner("Loading video information..."):
            video_info = get_video_info(url)
        
        if video_info:
            # Display video information
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(video_info['thumbnail'], width=200)
            
            with col2:
                st.subheader(video_info['title'])
                st.write(f"**Duration:** {video_info['duration']}")
            
            # Quality selection
            st.subheader("Select Video Quality")
            
            if video_info['video_streams']:
                # Create quality options
                quality_options = []
                for resolution, stream_info in video_info['video_streams']:
                    quality_text = f"{resolution} ({stream_info['fps']}fps) - {stream_info['size']}"
                    quality_options.append((quality_text, stream_info['stream']))
                
                selected_quality = st.selectbox(
                    "Choose quality:",
                    options=range(len(quality_options)),
                    format_func=lambda x: quality_options[x][0]
                )
                
                # Thread selection
                threads = st.slider("Download Threads (higher = faster):", min_value=1, max_value=64, value=32)
                
                # Download button
                if st.button("Download Video", type="primary", use_container_width=True):
                    selected_stream = quality_options[selected_quality][1]
                    video_url = selected_stream.url
                    audio_url = video_info['audio_stream'].url if video_info['audio_stream'] else None
                    
                    if not audio_url:
                        st.error("No audio stream found for this video")
                    else:
                        # Start download with modular approach
                        download_with_modular_approach(
                            video_url, 
                            audio_url, 
                            video_info['title'], 
                            threads
                        )
            else:
                st.error("No video streams available for this video")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and modular Python architecture")

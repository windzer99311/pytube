#!/usr/bin/env python3
"""
Simple Fast Downloader - Easy-to-use high-performance file downloader

This script provides a simple way to download files with browser-like speeds.
Just edit the URLs at the top of this file and run it.
"""
import colorama
import os
from optimized_Chunk_list import video_byte_range, audio_byte_range
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import requests
from requests.adapters import HTTPAdapter

# Import Retry from urllib3 (this is available because requests installs urllib3)
try:
    from urllib3.util.retry import Retry
except ImportError:
    # Fallback in case direct import fails, use the one from requests
    # Just import directly - both packages are installed
    import urllib3
    from urllib3.util.retry import Retry

def start(video_stream, audio_stream, thread, video_file, audio_file):
    """Main function to start the download process with given parameters"""
    global VIDEO_URL, AUDIO_URL, VIDEO_OUTPUT, AUDIO_OUTPUT, THREADS, vid_detail, aud_detail, DOWNLOAD_AUDIO
    VIDEO_URL = video_stream
    AUDIO_URL = audio_stream
    VIDEO_OUTPUT = video_file  # Output filename for main download
    AUDIO_OUTPUT = audio_file
    # Number of download threads (more threads = faster download, but too many might cause issues)
    THREADS = thread
    vid_detail = video_byte_range(VIDEO_URL, THREADS)
    aud_detail = audio_byte_range(AUDIO_URL, THREADS)
    # This will be automatically set based on whether AUDIO_URL is provided
    DOWNLOAD_AUDIO = bool(AUDIO_URL)

    # -----------------------------------------------------------
    # DO NOT MODIFY BELOW THIS LINE
    # -----------------------------------------------------------

    # Settings
    DEFAULT_CHUNK_SIZE = 1024 * 256  # 256KB chunks for better network compatibility
    DEFAULT_TIMEOUT = 15  # Balanced timeout for reliability and speed
    MAX_CONNECTIONS_PER_HOST = 4  # Reduced connections to prevent network saturation
    BUFFER_SIZE = 1024 * 512  # 512KB buffer size for optimal throughput
    TEMP_FOLDER = "temp_download_chunks"  # Folder to store temporary chunk files

    # Create temp folder if it doesn't exist
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)

    # Configure colorful output if platform supports it
    try:
        colorama.init()
        GREEN = colorama.Fore.GREEN
        YELLOW = colorama.Fore.YELLOW
        RED = colorama.Fore.RED
        BLUE = colorama.Fore.BLUE
        RESET = colorama.Style.RESET_ALL
    except ImportError:
        GREEN = YELLOW = RED = BLUE = RESET = ""

    def format_size(size_bytes):
        """Format bytes into a human-readable string."""
        units = ['B', 'KB', 'MB', 'GB']
        unit_index = 0

        if size_bytes is None or size_bytes == 0:
            return "0 B"

        size_bytes = float(size_bytes)
        for unit in units:
            if size_bytes < 1024.0 or unit == 'GB':
                break
            size_bytes /= 1024.0
            unit_index += 1

        return f"{size_bytes:.2f} {units[unit_index]}"

    def format_time(seconds):
        """Format seconds into a human-readable time string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds %= 60
            return f"{minutes:.0f}m {seconds:.0f}s"
        else:
            hours = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60
            return f"{hours:.0f}h {minutes:.0f}m {seconds:.0f}s"

    def download_chunk(url, start, end, temp_file, chunk_id, callback=None, max_retries=3):
        """Download a specific chunk of a file with retry logic and performance optimization."""
        retries = 0

        # Create an optimized session for connection pooling
        session = requests.Session()

        # Configure the session for better performance
        retry_strategy = Retry(
            total=0,  # We'll handle retries manually
            connect=0,
            read=0,
            status=0,
            other=0
        )

        adapter = HTTPAdapter(
            pool_connections=MAX_CONNECTIONS_PER_HOST,
            pool_maxsize=MAX_CONNECTIONS_PER_HOST,
            max_retries=retry_strategy,
            pool_block=False
        )
        session.mount('https://', adapter)
        session.mount('http://', adapter)

        while retries < max_retries:
            try:
                # Optimize headers for faster connection
                headers = {
                    'Range': f'bytes={start}-{end}',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Connection': 'keep-alive',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'max-age=0',
                    'Accept': '*/*',
                    'DNT': '1',
                    'TE': 'trailers'
                }

                # Early callback to notify that download has started or retried
                if callback:
                    callback(chunk_id, 0)

                # Use stream=True for better performance with large files
                response = session.get(
                    url,
                    headers=headers,
                    timeout=DEFAULT_TIMEOUT,
                    stream=True
                )
                response.raise_for_status()

                # Get the expected content length
                content_length = int(response.headers.get('Content-Length', end - start + 1))

                # Use BytesIO for in-memory buffering (reduces disk I/O overhead)
                buffer = BytesIO()
                total_received = 0

                # Using our optimized buffer size for better throughput
                buffer_size = BUFFER_SIZE
                update_threshold = max(buffer_size, content_length // 10)  # Update progress at most 10 times
                last_update = 0

                # Download with performance-optimized parameters
                for chunk in response.iter_content(chunk_size=buffer_size):
                    if chunk:  # Filter out keep-alive chunks
                        buffer.write(chunk)
                        total_received += len(chunk)

                        # Update progress less frequently for better performance
                        if callback and (total_received - last_update >= update_threshold):
                            callback(chunk_id, total_received)
                            last_update = total_received

                # Write the entire buffer to disk at once (faster than multiple small writes)
                with open(temp_file, 'wb') as f:
                    f.write(buffer.getvalue())

                # Final callback with total size
                if callback and total_received > 0:
                    callback(chunk_id, total_received)

                # Cleanup
                buffer.close()
                session.close()

                # Successful download
                return True

            except requests.exceptions.RequestException as e:
                retries += 1
                print(f"{YELLOW}Connection error on chunk {chunk_id} (attempt {retries}/{max_retries}): {e}{RESET}")
                if retries < max_retries:
                    # Exponential backoff with shorter initial times: 0.5s, 1s, 2s, etc.
                    wait_time = 0.5 * (2 ** (retries - 1))
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"{RED}Failed to download chunk {chunk_id} after {max_retries} attempts{RESET}")
                    session.close()
                    return False

            except Exception as e:
                print(f"{RED}Error downloading chunk {chunk_id}: {e}{RESET}")
                session.close()
                return False

    def download_chunk_wrapper(args):
        """Wrapper function to unpack arguments for download_chunk from a tuple."""
        return download_chunk(*args)

    def truly_parallel_download():
        """Download files simultaneously with true parallelism.

        This function implements a truly immediate and interleaved approach to downloading
        file chunks. Each chunk starts downloading as soon as it's created, without
        waiting for other chunks to be prepared first. For multiple files, tasks are created
        and started in alternating order.

        Benefits:
        - Immediate start: Each chunk begins downloading as soon as it's created
        - Better parallelism by distributing different types of downloads
        - More efficient resource utilization by interleaving different media types
        - Prevention of network bottlenecks by avoiding sequential processing
        - Faster startup by eliminating the delay between setup and download start
        """
        # Allow access to the global configuration variables
        global DOWNLOAD_AUDIO, VIDEO_URL, AUDIO_URL, VIDEO_OUTPUT, AUDIO_OUTPUT, THREADS
        # TEMP_FOLDER is defined locally in the start function
        # Removed print statements to keep the interface clean for Streamlit

        # Start the timer
        start_time = time.time()

        # Get file sizes
        video_size = vid_detail[1]
        if not video_size:
            print(f"{RED}Unable to get video file size. Aborting download.{RESET}")
            return False

        audio_size = 0
        if DOWNLOAD_AUDIO:
            audio_size = aud_detail[1]
            if not audio_size:
                print(f"{RED}Unable to get audio file size. Skipping audio download.{RESET}")
                DOWNLOAD_AUDIO = False

        # Create temporary files for each chunk
        video_temp_files = vid_detail[0]
        audio_temp_files = aud_detail[0]

        # Setup progress tracking
        video_downloaded = [0] * THREADS
        audio_downloaded = [0] * THREADS if DOWNLOAD_AUDIO else []
        last_progress_time = time.time()

        # Calculate total sizes
        video_total_size = sum(end - start + 1 for start, end, _ in video_temp_files)
        audio_total_size = sum(end - start + 1 for start, end, _ in audio_temp_files) if DOWNLOAD_AUDIO else 0
        video_last_bytes = 0
        audio_last_bytes = 0

        def make_video_callback(index):
            def callback(chunk_id, chunk_size):
                nonlocal video_downloaded, last_progress_time, video_last_bytes
                video_downloaded[index] = chunk_size
                # Update progress less frequently for better performance
                update_progress()

            return callback

        def make_audio_callback(index):
            def callback(chunk_id, chunk_size):
                nonlocal audio_downloaded, last_progress_time, audio_last_bytes
                audio_downloaded[index] = chunk_size
                # Update progress less frequently for better performance
                update_progress()

            return callback

        def update_progress():
            nonlocal last_progress_time, video_last_bytes, audio_last_bytes

            now = time.time()
            interval = now - last_progress_time

            # Remove the time interval check for true real-time updates
            # Video progress
            video_total_downloaded = sum(video_downloaded)
            video_percent = (video_total_downloaded / video_total_size * 100) if video_total_size > 0 else 0

            # Only calculate speed when enough time has passed for accurate measurement
            if interval >= 0.1:  # More frequent speed updates (10 times per second)
                video_bytes_since_last = video_total_downloaded - video_last_bytes
                video_speed = video_bytes_since_last / interval if interval > 0 else 0

                # Calculate ETA for video
                if video_speed > 0 and video_total_downloaded < video_total_size:
                    video_eta = (video_total_size - video_total_downloaded) / video_speed
                    video_eta_str = format_time(video_eta)
                else:
                    video_eta_str = "Completed" if video_total_downloaded >= video_total_size else "Calculating..."

                # Update last values for speed calculations
                last_progress_time = now
                video_last_bytes = video_total_downloaded

                # Print real-time progress immediately for Streamlit to capture
                print(f"Video: [{'=' * int(video_percent / 5):<20}] {video_percent:.2f}% at {format_size(video_speed)}/s ETA: {video_eta_str}")

            # Audio progress (if applicable)
            if DOWNLOAD_AUDIO:
                audio_total_downloaded = sum(audio_downloaded)
                audio_percent = (audio_total_downloaded / audio_total_size * 100) if audio_total_size > 0 else 0

                # Only calculate speed when enough time has passed
                if interval >= 0.1:  # More frequent speed updates
                    audio_bytes_since_last = audio_total_downloaded - audio_last_bytes
                    audio_speed = audio_bytes_since_last / interval if interval > 0 else 0

                    # Calculate ETA for audio
                    if audio_speed > 0 and audio_total_downloaded < audio_total_size:
                        audio_eta = (audio_total_size - audio_total_downloaded) / audio_speed
                        audio_eta_str = format_time(audio_eta)
                    else:
                        audio_eta_str = "Completed" if audio_total_downloaded >= audio_total_size else "Calculating..."

                    # Update last values for speed calculations
                    audio_last_bytes = audio_total_downloaded

                    # Print real-time progress immediately for Streamlit to capture
                    print(f"Audio: [{'=' * int(audio_percent / 5):<20}] {audio_percent:.2f}% at {format_size(audio_speed)}/s ETA: {audio_eta_str}")

        # Create a ThreadPoolExecutor for true parallelism
        with ThreadPoolExecutor(max_workers=THREADS * 2 if DOWNLOAD_AUDIO else THREADS) as executor:
            futures = {}

            # Submit video chunks immediately as they're created
            for i, (start, end, temp_file) in enumerate(video_temp_files):
                future = executor.submit(
                    download_chunk,
                    VIDEO_URL,
                    start,
                    end,
                    temp_file,
                    f"video_{i}",
                    make_video_callback(i)
                )
                futures[future] = ('video', i, temp_file)

            # Submit audio chunks (if audio download is enabled) interleaved with video
            if DOWNLOAD_AUDIO:
                for i, (start, end, temp_file) in enumerate(audio_temp_files):
                    future = executor.submit(
                        download_chunk,
                        AUDIO_URL,
                        start,
                        end,
                        temp_file,
                        f"audio_{i}",
                        make_audio_callback(i)
                    )
                    futures[future] = ('audio', i, temp_file)

            # Wait for all chunks to complete
            failed_chunks = []
            for future in as_completed(futures):
                file_type, chunk_index, temp_file = futures[future]
                try:
                    success = future.result()
                    if not success:
                        failed_chunks.append((file_type, chunk_index, temp_file))
                except Exception as e:
                    print(f"{RED}Exception in {file_type} chunk {chunk_index}: {e}{RESET}")
                    failed_chunks.append((file_type, chunk_index, temp_file))

        # Check if any chunks failed
        if failed_chunks:
            print(f"{RED}Failed to download {len(failed_chunks)} chunks. Aborting.{RESET}")
            return False

        # Merge video chunks
        print(f"{GREEN}Merging video chunks...{RESET}")
        try:
            with open(VIDEO_OUTPUT, 'wb') as output_file:
                for i in range(THREADS):
                    temp_file = f"temp_download_chunks/video_part{i}.mp4"
                    if os.path.exists(temp_file):
                        with open(temp_file, 'rb') as chunk_file:
                            output_file.write(chunk_file.read())
                        os.remove(temp_file)  # Clean up temp file
        except Exception as e:
            print(f"{RED}Error merging video chunks: {e}{RESET}")
            return False

        # Merge audio chunks (if audio was downloaded)
        if DOWNLOAD_AUDIO:
            print(f"{GREEN}Merging audio chunks...{RESET}")
            try:
                with open(AUDIO_OUTPUT, 'wb') as output_file:
                    for i in range(THREADS):
                        temp_file = f"temp_download_chunks/audio_part{i}.m4a"
                        if os.path.exists(temp_file):
                            with open(temp_file, 'rb') as chunk_file:
                                output_file.write(chunk_file.read())
                            os.remove(temp_file)  # Clean up temp file
            except Exception as e:
                print(f"{RED}Error merging audio chunks: {e}{RESET}")
                return False

        # Calculate and display final statistics
        end_time = time.time()
        total_time = end_time - start_time
        total_downloaded = video_total_size + audio_total_size
        average_speed = total_downloaded / total_time if total_time > 0 else 0

        print(f"{GREEN}Download completed successfully!{RESET}")
        print(f"Total time: {format_time(total_time)}")
        print(f"Total downloaded: {format_size(total_downloaded)}")
        print(f"Average speed: {format_size(average_speed)}/s")

        return True

    # Start the download process
    return truly_parallel_download()

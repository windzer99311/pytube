from pytubefix import YouTube
def main(context):
    # Log some info to the Appwrite console
    link="https://www.youtube.com/watch?v=Jtauh8GcxBY"

    if not link:
        return context.res.json({"error": "No link provided"}, 400)

    # These options help bypass bot detection
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        # This emulates a real browser
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            print("title:",info.get('title'),"stream:",info.get('url'))
    except Exception as e:
        print(e)

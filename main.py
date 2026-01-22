from pytubefix import YouTube
def main(context):
    # Log some info to the Appwrite console
    url="https://www.youtube.com/watch?v=Jtauh8GcxBY"
    yt=YouTube(url).streams.first().url
    print(yt)
    
    return context.res.json({
        "message": f"Hello {yt}!",
        "method": method,
        "status": "success"
    })

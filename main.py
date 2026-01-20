from fastapi import FastAPI
import requests
from pytubefix import YouTube

app = FastAPI()
@app.get("/search")
def get_url(url: str):
    yt=YouTube(url)
    link = yt.streams.get_by_itag(139).url
    return link

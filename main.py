from fastapi import FastAPI
import requests

app = FastAPI()
@app.get("/search")
def get_stream(url: str):
    api = "https://api.vidssave.com/api/contentsite_api/media/parse"

    data = {
        "auth": "20250901majwlqo",
        "domain": "api-ak.vidssave.com",
        "origin": "source",
        "link": url,
    }

    r = requests.post(api, data=data)
    return r.text

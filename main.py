from fastapi import FastAPI
import requests

app = FastAPI()
@app.get("/search")
def get_stream(url: str):
    api = "https://api.vidssave.com/api/contentsite_api/media/parse"

    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://vidssave.com",
        "referer": "https://vidssave.com/",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
    }

    data = {
        "auth": "20250901majwlqo",
        "domain": "api-ak.vidssave.com",
        "origin": "source",
        "link": url,
    }

    r = requests.post(api, headers=headers, data=data)
    print(r.status_code)
    return r.text

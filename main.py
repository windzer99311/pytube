from fastapi import FastAPI
import requests

app = FastAPI()
@app.get("/search")
def get_stream(url: str):
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "if-none-match": 'W/"1da-9kqxJsN/A8wyW0Pt99w9jZk0IQ0"',
        "origin": "https://www.yt2mp3converter.net",
        "priority": "u=1, i",
        "referer": "https://www.yt2mp3converter.net/",
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
    }


    api = "https://api.vidssave.com/api/contentsite_api/media/parse"
    params = {
        "auth": "20250901majwlqo",
        "domain": "pi-ak.vidssave.com",
        "origin": "source",
        "link": url
    }

    r = requests.get(api, headers=headers, params=params)
    return r.text

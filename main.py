from fastapi import FastAPI
import requests
import uvicorn

app = FastAPI()

@app.get("/search")
def get_stream(url: str):
    api = "https://api.vidssave.com/api/contentsite_api/media/parse"

    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://vidssave.com",
        "referer": "https://vidssave.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    data = {
        "auth": "20250901majwlqo",
        "domain": "api-ak.vidssave.com",
        "origin": "source",
        "link": url
    }

    r = requests.post(api, headers=headers, data=data, timeout=15)

    return {
    "status_code": r.status_code,
    "headers": dict(r.headers),
    "body": r.text
}

if __name__ == "__main__":
    uvicorn.run(app)


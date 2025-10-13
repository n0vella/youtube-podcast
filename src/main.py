import datetime
import re

import requests
from flask import Flask, Response, request
from flask_caching import Cache
from flask_cors import CORS

from src.api import Video, get_channel_id, get_channel_info, get_channel_videos
from src.audio import get_audio_link
from src.feed import generate_feed

app = Flask(__name__)
CORS(app)
cache = Cache(app, config={"CACHE_TYPE": "simple"})


@app.route("/feed/<string:channel_name>")
def get_channel_feed(channel_name: str) -> Response:
    # get url args
    min_duration = request.args.get("min_duration", default=None, type=int)
    max_duration = request.args.get("max_duration", default=None, type=int)

    channel_id = get_channel_id(channel_name)

    channel_info = get_channel_info(channel_id)
    videos = get_channel_videos(channel_id)

    def filter_results(video: Video) -> bool:
        return not (
            (min_duration and video["duration"] < min_duration)
            or (max_duration and video["duration"] > max_duration)
        )

    videos = filter(filter_results, videos)

    feed_xml = generate_feed(channel_info, videos, request.url_root)
    return Response(feed_xml, mimetype="application/xml")


CHUNK_SIZE = 1024 * 1024 * 10


@app.route("/audio/<string:video_id>")
def get_audio(video_id: str):
    url = cache.get(video_id) or get_audio_link(video_id)

    expire = re.search(r"expire=(\d{10,})", url).group(1)

    timeout = int(expire) - datetime.datetime.now(tz=datetime.UTC).timestamp()

    cache.set(video_id, url, timeout=int(timeout))

    # minimal browser-like headers
    h = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }

    # get total size via HEAD
    head = requests.head(url, headers=h, timeout=10, allow_redirects=True)
    total = head.headers.get("Content-Length", 0)
    mimetype = head.headers.get("Content-Type", "audio/mp4")

    # check if client wants a range (seeking support)
    client_range = request.headers.get("Range")
    if client_range:
        # proxy single range request directly (for seek)
        upstream = requests.get(
            url,
            headers={**h, "Range": client_range},
            stream=True,
            timeout=15,
        )

        # return response from YouTube mantaining some headers
        resp = Response(
            upstream.iter_content(256 * 1024),
            status=upstream.status_code,
            mimetype=mimetype,
            direct_passthrough=True,
        )
        for key in ("Content-Range", "Content-Length", "Accept-Ranges"):
            if val := upstream.headers.get(key):
                resp.headers[key] = val
        return resp

    # full download: use chunked range requests to avoid throttling
    def generate():
        pos = 0
        total_int = int(total) if total else pos + CHUNK_SIZE
        while pos < total_int:
            rng = f"bytes={pos}-{min(pos + CHUNK_SIZE, total_int) - 1}"
            r = requests.get(url, headers={**h, "Range": rng}, stream=True, timeout=15)

            if r.status_code not in (200, 206):
                break

            yield from r.iter_content(256 * 1024)

            # once there is no more chunks
            # parse Content-Range to get real position data
            if "Content-Range" in r.headers:
                cr = r.headers["Content-Range"]
                start, end = re.match(r"^.+-(\d+)/(\d+)", cr).groups()
                pos = int(start) + 1
                if end.isdigit():
                    total_int = int(end)
                    response_headers["Content-Length"] = end

    response_headers = {
        "Content-Length": total,
        "Accept-Ranges": "bytes",
    }

    return Response(
        generate(),
        headers=response_headers,
        mimetype=mimetype,
        direct_passthrough=True,
    )

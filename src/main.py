import re
from datetime import datetime, timezone

import requests
from flask import Flask, Response, redirect, request, stream_with_context
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

    feed_xml = generate_feed(channel_info, videos)
    return Response(feed_xml, mimetype="application/xml")


@app.route("/audio/<string:video_id>")
def get_audio(video_id: str) -> Response:
    audio_url = cache.get(video_id)
    if audio_url:
        return redirect(audio_url)

    audio_url = get_audio_link(video_id)

    expire = re.search(r"expire=(\d{10,})", audio_url).group(1)

    timeout = datetime.fromtimestamp(int(expire), tz=timezone.utc) - datetime.now(
        tz=timezone.utc,
    )

    cache.set(video_id, audio_url, timeout=int(timeout.seconds))

    response = requests.get(audio_url, stream=True, timeout=5)

    return Response(
        stream_with_context(response.iter_content(chunk_size=1024)),
        content_type=response.headers.get("content-type", "audio/mpeg"),
    )

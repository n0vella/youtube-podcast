from flask import Flask, Response, redirect, request
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


@app.route("/audio/<string:video_id>")
def get_audio(video_id: str) -> Response:
    audio_url = get_audio_link(video_id)

    return redirect(audio_url, code=302)

from flask import Flask, Response
from flask_caching import Cache
from flask_cors import CORS

from src.api import get_channel_id, get_channel_info, get_channel_videos
from src.feed import generate_feed

app = Flask(__name__)
CORS(app)
cache = Cache(app, config={"CACHE_TYPE": "simple"})


@app.route("/feed/<string:channel_name>")
def get_channel_feed(channel_name: str) -> Response:
    channel_id = get_channel_id(channel_name)

    channel_info = get_channel_info(channel_id)
    videos = get_channel_videos(channel_id)

    feed_xml = generate_feed(channel_info, videos)
    return Response(feed_xml, mimetype="application/xml")

# ruff: noqa: T201

from yt2podcast.api import get_channel_id, get_channel_videos

channel_id = get_channel_id("LordDraugr")

print("CHANNEL_ID:", channel_id)

videos = get_channel_videos(channel_id)

for video in videos:
    print(video["video_id"], video["title"], video["published_at"])

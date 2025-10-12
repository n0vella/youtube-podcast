from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.api import Video


STORAGE_PATH = Path("./feeds")

STORAGE_PATH.mkdir(exist_ok=True)


def save_videos(channel_id: str, videos: list[Video]) -> bool | list[Video]:
    """returns: true when any passed video is already on storage and the entire feed"""
    file = STORAGE_PATH / (channel_id + ".json")
    file_updated = False  # any of the checked videos was already on storage

    if file.exists():
        with file.open() as f:
            previous_videos = json.load(f)

        previous_videos_ids = [v["video_id"] for v in previous_videos]
        new_videos: list[Video] = []

        for video in videos:
            if video["video_id"] in previous_videos_ids:
                file_updated = True
                break

            new_videos.append(video)

    else:
        new_videos = videos
        previous_videos = []

    feed = new_videos + previous_videos
    feed.sort(key=lambda v: v["published_at"], reverse=True)

    if new_videos:
        with file.open("w") as f:
            json.dump(
                feed,
                f,
                indent=2,
            )

    return file_updated, feed

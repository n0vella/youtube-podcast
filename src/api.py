from __future__ import annotations

import os
import re
from datetime import datetime
from typing import TypedDict

from googleapiclient.discovery import build


class ChannelInfo(TypedDict):
    id: str
    title: str
    description: str
    thumbnail_url: str


class Video(TypedDict):
    video_id: str
    title: str
    description: str
    thumbnail_url: str
    published_at: datetime
    duration: int


class ChannelNotFoundError(Exception):
    pass


youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))


def get_channel_id(channel_name: str) -> str:
    if channel_name.startswith("@"):
        channel_name = channel_name[1:]

    r = (
        youtube.search()
        .list(
            part="snippet",
            q=channel_name,
            type="channel",
            maxResults=1,
        )
        .execute()
    )

    if not r.get("items"):
        raise ChannelNotFoundError(channel_name + " is not a valid YouTube channel")

    return r["items"][0]["id"]["channelId"]


def get_channel_info(channel_id: str) -> ChannelInfo:
    r = (
        youtube.channels()
        .list(
            part="snippet",
            id=channel_id,
        )
        .execute()
    )

    channel = r["items"][0]["snippet"]

    return {
        "id": channel_id,
        "title": channel["title"],
        "description": channel["description"],
        "thumbnail_url": channel["thumbnails"]["high"]["url"],
    }


def get_video_durations(video_ids: list[str]) -> list[int]:
    r = (
        youtube.videos()
        .list(
            part="contentDetails",
            id=",".join(video_ids),
        )
        .execute()
    )

    durations = []

    for item in r["items"]:
        raw_duration = item["contentDetails"]["duration"]

        parsed_duration = re.match(
            r"PT(?:(?P<h>\d+)H)?(?:(?P<m>\d{1,2})M)?((?P<s>\d{1,2})S)?",
            raw_duration,
        )
        time = parsed_duration.groupdict()

        seconds = 0
        if time["h"]:
            seconds += int(time["h"]) * 3600
        if time["m"]:
            seconds += int(time["m"]) * 60
        if time["s"]:
            seconds += int(time["s"])

        durations.append(seconds)

    return durations


def get_channel_videos(channel_id: str) -> list[Video]:
    # Getting playlist id from channel
    r = (
        youtube.channels()
        .list(
            part="contentDetails",
            id=channel_id,
        )
        .execute()
    )

    uploads_playlist_id = r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    api_args = {
        "part": "snippet",
        "playlistId": uploads_playlist_id,
        "maxResults": 50,
    }

    results: list[Video] = []

    while True:
        # search api endpoint doesn't work well
        r = youtube.playlistItems().list(**api_args).execute()
        next_page_token = r.get("nextPageToken")

        videos = r.get("items", [])

        video_ids = [video["snippet"]["resourceId"]["videoId"] for video in videos]
        durations = get_video_durations(video_ids)

        for video, duration in zip(videos, durations):
            result: Video = {
                "video_id": video["snippet"]["resourceId"]["videoId"],
                "title": video["snippet"]["title"],
                "description": video["snippet"]["description"],
                "published_at": datetime.strptime(
                    video["snippet"]["publishedAt"],
                    "%Y-%m-%dT%H:%M:%S%z",
                ),
                "thumbnail_url": video["snippet"]["thumbnails"]["high"]["url"],
                "duration": duration,
            }
            results.append(result)

        if next_page_token:
            api_args["pageToken"] = next_page_token
        else:
            break

    return results

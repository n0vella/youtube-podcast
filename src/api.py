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
    api_args = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": 50,
        "order": "date",
        "type": "video",
    }

    results: list[Video] = []

    while True:
        r = youtube.search().list(**api_args).execute()
        next_page_token = r.get("nextPageToken")

        videos = r.get("items", [])

        durations = get_video_durations([video["id"]["videoId"] for video in videos])

        for video, duration in zip(videos, durations):
            result: Video = {}

            result["video_id"] = video["id"]["videoId"]
            snippet = video["snippet"]

            result["title"] = snippet["title"]
            result["description"] = snippet["description"]
            result["published_at"] = datetime.strptime(
                snippet["publishedAt"],
                "%Y-%m-%dT%H:%M:%S%z",
            )
            result["thumbnail_url"] = snippet["thumbnails"]["high"]["url"]
            result["duration"] = duration

            results.append(result)

        # keep fetching till the last page
        if next_page_token:
            api_args["pageToken"] = next_page_token
        else:
            break

    return results

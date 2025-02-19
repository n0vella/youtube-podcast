from __future__ import annotations

import os
from datetime import datetime
from typing import TypedDict

from googleapiclient.discovery import build


class ChannelInfo(TypedDict):
    title: str
    description: str
    thumbnail_url: str


class Video(TypedDict):
    video_id: str
    title: str
    description: str
    thumbnail_url: str
    published_at: datetime


class ChannelNotFoundError(Exception):
    pass


youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))


def get_channel_id(channel_name: str) -> str:
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
        "title": channel["title"],
        "description": channel["description"],
        "thumbnail_url": channel["thumbnails"]["high"]["url"],
    }


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

        for video in videos:
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

            results.append(result)

        # keep fetching till the last page
        if next_page_token:
            api_args["pageToken"] = next_page_token
        else:
            break

    return results

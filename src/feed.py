from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import urljoin

if TYPE_CHECKING:
    from src.api import ChannelInfo, Video


def generate_feed(channel_info: ChannelInfo, videos: list[Video], root_url: str) -> str:
    # create xml headers
    # root
    rss = ET.Element("rss")
    rss.set("version", "2.0")
    rss.attrib["xmlns:itunes"] = "http://www.itunes.com/dtds/podcast-1.0.dtd"

    # channel
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = channel_info["title"]
    ET.SubElement(channel, "link").text = (
        "https://www.youtube.com/channel/" + channel_info["id"]
    )
    image = ET.SubElement(channel, "image")
    ET.SubElement(image, "url").text = channel_info["thumbnail_url"]

    # add items from videos
    for video in videos:
        item = ET.SubElement(channel, "item")

        video_id = video["video_id"]

        ET.SubElement(item, "title").text = video["title"]
        ET.SubElement(item, "description").text = video.get("description", "")
        ET.SubElement(item, "pubDate").text = datetime.fromtimestamp(
            video.get("published_at"),
            tz=UTC,
        ).isoformat()
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set(
            "url",
            urljoin(os.getenv("SERVER_URL"), f"{root_url}audio/{video_id}"),
        )
        enclosure.set("type", "audio/mpeg")
        ET.SubElement(item, "itunes:image").set(
            "href",
            video.get("thumbnail_url", channel.get("thumbnail_url", "")),
        )
        ET.SubElement(item, "itunes:duration").text = str(video.get("duration", 0))

    return ET.tostring(rss)

# ruff: noqa: T201

from src.api import get_channel_id, get_channel_info

channel_id = get_channel_id("LordDraugr")

print("CHANNEL_ID:", channel_id)

channel_info = get_channel_info(channel_id)

print(channel_info)

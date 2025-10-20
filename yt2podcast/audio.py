from yt_dlp import YoutubeDL

ydl_opts = {
    "format": "bestaudio/best",
    "extractaudio": True,
    "noplaylist": True,
    "quiet": True,
}


def get_audio_link(video_id: str) -> str:
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={video_id}",
            download=False,
        )

    return info["url"]

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from pymongo import MongoClient
from PIL import Image
from io import BytesIO
import base64
import requests

# MongoDB setup
client = MongoClient("uri")
db = client["media_impact_db"]
youtube_col = db["youtube_data"]

# Convertir thumbnail a base64
def image_to_base64_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"Error processing thumbnail: {e}")
        return None

# Obtener transcripción
def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry['text'] for entry in transcript])
    except:
        return None

# Playlist URL
playlist_url = "https://www.youtube.com/playlist?list=PLISuFiQTdKDWc1PjlgqIAm1Bzc38MoLa6"

# yt-dlp config
ydl_opts = {
    'quiet': True,
    'extract_flat': True,
    'force_generic_extractor': True,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    playlist_info = ydl.extract_info(playlist_url, download=False)
    videos = playlist_info.get("entries", [])
    print(f"Found {len(videos)} videos in the playlist.")

    for video in videos:
        try:
            video_id = video.get("id")
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Extraer info detallada del vídeo
            video_info = ydl.extract_info(video_url, download=False)

            title = video_info.get("title")
            publish_date = video_info.get("upload_date")  # formato YYYYMMDD
            channel = video_info.get("channel")
            thumbnail_url = video_info.get("thumbnail")

            # Formatear fecha
            publish_date = f"{publish_date[:4]}-{publish_date[4:6]}-{publish_date[6:]}" if publish_date else None

            transcript = get_transcript(video_id)
            thumbnail_base64 = image_to_base64_from_url(thumbnail_url)

            doc = {
                "video_id": video_id,
                "video_url": video_url,
                "title": title,
                "publish_date": publish_date,
                "channel": channel,
                "thumbnail_base64": thumbnail_base64,
                "transcript_text": transcript
            }

            youtube_col.update_one(
                {"video_id": video_id},
                {"$set": doc},
                upsert=True
            )

            print(f"Stored video: {title}")

        except Exception as e:
            print(f"Error processing video: {e}")

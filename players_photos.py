from pymongo import MongoClient
from bs4 import BeautifulSoup
import requests
from PIL import Image
from io import BytesIO
import base64
import time

# MongoDB connection setup
client = MongoClient("uri")
db = client["media_impact_db"]
clubs_col = db["clubs"]       # Collection containing club info (name, squad URL)
players_col = db["players"]   # Collection containing player data

# Headers to simulate a real browser and avoid being blocked
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Function to download an image from a URL and convert it to base64
def image_to_base64_from_url(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")  # Convert to RGB to avoid format issues
        buffered = BytesIO()
        img.save(buffered, format="JPEG")  # Save image to memory buffer in JPEG format
        return base64.b64encode(buffered.getvalue()).decode("utf-8")  # Convert to base64 string
    except Exception as e:
        print(f" Error downloading image: {e}")
        return None

# Function to update missing player photos (only if the photo is not already stored)
def player_photos(club_name, squad_url):
    print(f"\n Checking {club_name}...")

    try:
        # Request the squad page
        res = requests.get(squad_url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # Locate the main player table
        table = soup.find("table", class_="items")
        if not table:
            print(f" No table found for {club_name}")
            return

        # Get all player rows (odd/even row classes)
        rows = table.find("tbody").find_all("tr", class_=["odd", "even"])

        for row in rows:
            try:
                # Extract player name
                name_tag = row.select_one("td.hauptlink a")
                if not name_tag:
                    continue
                name = name_tag.text.strip()
                # Find the player in the database
                player = players_col.find_one({"name": name, "club_name": club_name})

                # Skip if not found or already has a photo
                if not player or player.get("photo_base64"):
                    continue

                # Look for the player's image in the row
                img_tag = row.select_one("img.bilderrahmen-fixed")
                photo_url = img_tag.get("data-src") or img_tag.get("src") if img_tag else None
                photo_base64 = image_to_base64_from_url(photo_url) if photo_url else None

                # If successful, update the database with the photo
                if photo_base64:
                    players_col.update_one(
                        {"_id": player["_id"]},
                        {"$set": {"photo_base64": photo_base64}}
                    )
                    print(f" Photo updated for {name}")
                else:
                    print(f" No image found for {name}")

                time.sleep(1.5)  # Respectful pause to avoid overloading the server

            except Exception as e:
                print(f" Error processing player: {e}")
                continue

    except Exception as e:
        print(f" Error processing club {club_name}: {e}")

# Run the photo update function for every club in the database
clubs = list(clubs_col.find())

print(f"\n Starting photo insert for {len(clubs)} clubs...")

for club in clubs:
    club_name = club["club_name"]
    squad_url = club["squad_url"]
    player_photos(club_name, squad_url)
    time.sleep(2)  # Delay between clubs

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from PIL import Image
from io import BytesIO
import base64
import time

# MongoDB setup
client = MongoClient("mongodb+srv://arabelacarceles:MongoTest123@cluster0.0wssh1x.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["media_impact_db"]
clubs_col = db["clubs"]
players_col = db["players"]

# User-Agent
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def image_to_base64_from_url(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"Error downloading photo: {e}")
        return None

def scrape_players_from_club(club_name, squad_url):
    print(f"\nAccessing squad for {club_name}")
    try:
        res = requests.get(squad_url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        table = soup.find("table", class_="items")
        if not table:
            print(f"No player table found for {club_name}")
            return

        rows = table.find("tbody").find_all("tr", class_=["odd", "even"])

        for row in rows:
            try:
                name_tag = row.select_one("td.hauptlink a")
                if not name_tag:
                    continue

                name = name_tag.text.strip()
                profile_url = "https://www.transfermarkt.co.uk" + name_tag["href"]

                tds = row.find_all("td")

                age = tds[4].text.strip() if len(tds) > 4 else None
                position = row.find_all("tr")[-1].text.strip() if row.find("tr") else None
                nationality = tds[1].find("img")["title"] if tds[1].find("img") else None
                market_value = tds[-1].text.strip() if tds[-1] else None

                img_tag = row.select_one("img")
                photo_url = img_tag["src"] if img_tag and "portrait" in img_tag["src"] else None
                photo_base64 = image_to_base64_from_url(photo_url) if photo_url else None

                player_data = {
                    "name": name,
                    "profile_url": profile_url,
                    "position": position,
                    "age": age,
                    "nationality": nationality,
                    "market_value": market_value,
                    "club_name": club_name,
                    "photo_base64": photo_base64
                }

                players_col.update_one(
                    {"name": name, "club_name": club_name},
                    {"$set": player_data},
                    upsert=True
                )
                print(f"Inserted {name} from {club_name}".encode("ascii", errors="ignore").decode())

            except Exception as e:
                print(f"Error parsing player row: {e}")
                continue

    except Exception as e:
        print(f"Error fetching squad for {club_name}: {e}")

# Ejecutar scraping
clubs = list(clubs_col.find())

for club in clubs:
    club_name = club["club_name"]
    squad_url = club["squad_url"]
    scrape_players_from_club(club_name, squad_url)
    time.sleep(2)

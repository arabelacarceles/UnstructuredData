import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from PIL import Image
from io import BytesIO
import base64
import time

# MongoDB setup
client = MongoClient("uri")  # Replace with your actual URI
db = client["media_impact_db"]
clubs_col = db["clubs"]
players_col = db["players"]

# Scraping function for players
def scrape_players_from_club(club_name, squad_url):
    print(f"\n Accessing squad for {club_name}")
    try:
        res = requests.get(squad_url, headers={"User-Agent": "Mozilla/5.0"})
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        table = soup.find("table", class_="items")
        if not table:
            print(f" No player table found for {club_name}")
            return

        rows = table.find("tbody").find_all("tr", class_=["odd", "even"])
        print(f" Found {len(rows)} player rows")

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
                market_value = tds[-1].text.strip() if tds[-1] else None

                player_data = {
                    "name": name,
                    "profile_url": profile_url,
                    "position": position,
                    "age": age,
                    "market_value": market_value,
                    "club_name": club_name,
                }

                players_col.update_one(
                    {"name": name, "club_name": club_name},
                    {"$set": player_data},
                    upsert=True
                )
                print(f" Inserted: {name} from {club_name}".encode("ascii", errors="ignore").decode())

            except Exception as e:
                print(f" Error parsing player row: {e}")
                continue

    except Exception as e:
        print(f" Error fetching squad for {club_name}: {e}")

# Run scraping for all clubs
clubs = list(clubs_col.find())
print(f"\n Starting scraping for {len(clubs)} clubs...")

for club in clubs:
    club_name = club["club_name"]
    squad_url = club["squad_url"]
    scrape_players_from_club(club_name, squad_url)
    time.sleep(2)

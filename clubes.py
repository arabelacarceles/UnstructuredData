import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from PIL import Image
from io import BytesIO
import base64
import time

# MongoDB setup
client = MongoClient("uri")
db = client["media_impact_db"]
clubs_col = db["clubs"]

# Convertir imagen a base64
def image_to_base64(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        print(f" Error downloading image: {e}")
        return None

# Scraping config
base_url = "https://www.transfermarkt.co.uk"
pl_url = f"{base_url}/premier-league/startseite/wettbewerb/GB1"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(pl_url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

table = soup.find("table", class_="items")
if not table:
    print(" No table found on page.")
    exit()

rows = table.select("tbody tr")
print(f" Found {len(rows)} rows.")

for row in rows:
    try:
        # Club name and URL
        club_link = row.select_one('td a[title][href^="/"]')
        if not club_link:
            print(" Club link not found in row.")
            continue

        club_name = club_link["title"].strip()
        club_href = club_link["href"].strip()
        club_url = base_url + club_href.replace("startseite", "kader") + "/plus/1"

        # Club logo
        logo_img = row.select_one("td img")
        logo_url = logo_img.get("data-src") or logo_img.get("src") if logo_img else None
        logo_base64 = image_to_base64(logo_url) if logo_url else None

        # Store in MongoDB
        clubs_col.update_one(
            {"club_name": club_name},
            {"$set": {
                "club_name": club_name,
                "squad_url": club_url,
                "logo_base64": logo_base64
            }},
            upsert=True
        )

        print(f" Stored: {club_name}")
        time.sleep(0.5)

    except Exception as e:
        print(f" Error processing row: {e}")

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from PIL import Image
from io import BytesIO
import base64
import time

# MongoDB connection setup
client = MongoClient("uri")  
db = client["media_impact_db"] #database name
clubs_col = db["clubs"]  # This collection will store the Premier League clubs

# Function to convert an image URL to a base64 string
def image_to_base64(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raises HTTPError if the response was unsuccessful
        img = Image.open(BytesIO(response.content)).convert("RGB")  # Convert image to RGB
        buffered = BytesIO()
        img.save(buffered, format="JPEG")  # Save to memory in JPEG format
        return base64.b64encode(buffered.getvalue()).decode("utf-8")  # Encode image as base64 string
    except Exception as e:
        print(f" Error downloading image: {e}")
        return None

# Base URL and Premier League page URL
base_url = "https://www.transfermarkt.co.uk"
pl_url = f"{base_url}/premier-league/startseite/wettbewerb/GB1"  # URL for Premier League overview page
headers = {"User-Agent": "Mozilla/5.0"}

# Send request to the Premier League page and parse the HTML
response = requests.get(pl_url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Find the table with all Premier League clubs
table = soup.find("table", class_="items")
if not table:
    print(" No table found on page.")
    exit()

# Select all rows inside the table
rows = table.select("tbody tr")
print(f" Found {len(rows)} rows.")  # Number of clubs found

# Loop over each row to extract club data
for row in rows:
    try:
        # Find the anchor tag that contains the club name and relative link
        club_link = row.select_one('td a[title][href^="/"]')
        if not club_link:
            print(" Club link not found in row.")
            continue

        club_name = club_link["title"].strip()  # Club name
        club_href = club_link["href"].strip()  # Relative URL
        # Convert overview page to squad page URL (kader), adding "/plus/1" for full squad
        club_url = base_url + club_href.replace("startseite", "kader") + "/plus/1"

        # Get the club logo image
        logo_img = row.select_one("td img")
        # Prefer "data-src" over "src" for image URL
        logo_url = logo_img.get("data-src") or logo_img.get("src") if logo_img else None
        logo_base64 = image_to_base64(logo_url) if logo_url else None

        # Store or update club data in MongoDB
        clubs_col.update_one(
            {"club_name": club_name},  # Match on club name
            {"$set": {
                "club_name": club_name,
                "squad_url": club_url,
                "logo_base64": logo_base64
            }},
            upsert=True  # Insert if the club doesn't exist
        )

        print(f" Stored: {club_name}")
        time.sleep(0.5)  # Pause to avoid sending too many requests too quickly

    except Exception as e:
        print(f" Error processing row: {e}")

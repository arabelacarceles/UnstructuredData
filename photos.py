import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup
import base64
from PIL import Image
from io import BytesIO

# MongoDB connection
client = MongoClient("mongodb+srv://arabelacarceles:MongoTest123@cluster0.0wssh1x.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["media_impact_db"]
clubs_col = db["clubs"]

headers = {
    "User-Agent": "Mozilla/5.0"
}

updated_count = 0

for club in clubs_col.find():
    club_name = club["club_name"]
    squad_url = club.get("squad_url")

    if not squad_url:
        print(f"No squad_url for {club_name}")
        continue

    try:
        response = requests.get(squad_url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        # Buscar correctamente el contenedor de la imagen
        img_tag = soup.select_one("div.data-header__profile-container img")
        if not img_tag:
            print(f"No image tag found for: {club_name}")
            continue

        # Descargar la imagen
        img_url = img_tag["src"]
        if img_url.startswith("//"):
            img_url = "https:" + img_url

        img_response = requests.get(img_url, headers=headers, timeout=30)
        img = Image.open(BytesIO(img_response.content)).convert("RGB")

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        clubs_col.update_one(
            {"_id": club["_id"]},
            {"$set": {"logo_base64": img_base64}}
        )

        updated_count += 1
        print(f" Saved logo for: {club_name}")

    except Exception as e:
        print(f" Error processing {club_name}: {e}")

print(f"\n Total logos updated: {updated_count}")

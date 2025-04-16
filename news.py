from GoogleNews import GoogleNews
from newspaper import Article
import requests
from pymongo import MongoClient
import time
import unicodedata
import random

# MongoDB setup
mongo = MongoClient("uri")
db = mongo["media_impact_db"]
social_data_col = db["news_data"]
players_col = db["clubs"]

# GoogleNews config
googlenews = GoogleNews(lang='en', period='30d')

# Función para impresión segura
def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        text_ascii = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        print(text_ascii)

# Descargar artículo con headers
def download_article_with_headers(url):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        article = Article(url)
        article.set_html(response.text)
        article.parse()

        return {
            "title": article.title,
            "text": article.text
        }

    except Exception as e:
        safe_print(f"Could not download full article: {url}\n{e}")
        return None

# Buscar artículos de noticias
def scrape_news(player_name, required_articles=15):
    googlenews.clear()
    googlenews.search(player_name)

    articles = []
    page = 1

    while len(articles) < required_articles:
        results = googlenews.page_at(page)
        if not results:
            break

        for r in results:
            url = r["link"].split("&")[0]
            article_data = download_article_with_headers(url)

            if article_data and article_data["text"].strip():
                articles.append({
                    "title": article_data["title"],
                    "source": r.get("media", "Unknown"),
                    "date": r.get("date", "Unknown"),
                    "url": url,
                    "text": article_data["text"]
                })

                if len(articles) >= required_articles:
                    break

        page += 1
        #time.sleep(random.uniform(3, 6))  # Pausa aleatoria entre páginas

    return articles

# Guardar en MongoDB
def store_news(player_name, articles):
    if not articles:
        safe_print(f"No articles found for {player_name}")
        return

    social_data_col.insert_one({
        "club": player_name,
        "source": "news",
        "articles_count": len(articles),
        "articles": articles
    })
    safe_print(f"Stored {len(articles)} articles for {player_name}")

# Ejecutar para todos los jugadores
players = list(players_col.find())

for player in players:
    name = player["club_name"]

    # Skip si ya hay artículos guardados
    if social_data_col.count_documents({"club": name, "source": "news"}) > 0:
        safe_print(f"Skipping {name}, articles already exist.")
        continue

    safe_print(f"\nSearching news for: {name}")
    articles = scrape_news(name, required_articles=15)
    store_news(name, articles)
    #time.sleep(random.uniform(30, 60))  # Pausa aleatoria entre jugadores

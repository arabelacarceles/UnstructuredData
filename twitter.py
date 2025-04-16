import tweepy
from pymongo import MongoClient
from datetime import datetime
import time

# Twitter API setup
BEARER_TOKEN = ""
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# MongoDB setup
mongo = MongoClient("uri0")
db = mongo["media_impact_db"]
clubs_col = db["clubs"]
twitter_col = db["twitter_data"]

# Función para buscar tweets
def search_tweets_for_entity(name, max_results=20):
    query = f'"{name}" -is:retweet lang:en'
    tweets_data = []

    try:
        response = client.search_recent_tweets(query=query, max_results=max_results,
                                               tweet_fields=["created_at", "author_id", "text", "lang"])
        tweets = response.data
        if not tweets:
            return []

        for tweet in tweets:
            tweets_data.append({
                "date": tweet.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "author_id": tweet.author_id,
                "content": tweet.text
            })

    except Exception as e:
        print(f"Error fetching tweets for {name}: {e}")

    return tweets_data

# Guardar en MongoDB
def store_twitter_data(entity_name, tweets):
    if not tweets:
        print(f"No tweets found for {entity_name}")
        return False

    twitter_col.insert_one({
        "entity": entity_name,
        "source": "twitter",
        "mention_count": len(tweets),
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mentions_data": tweets
    })
    print(f"Stored {len(tweets)} tweets for {entity_name}")
    return True

# Bucle por todos los clubes
clubs = list(clubs_col.find())

for club in clubs:
    name = club["club_name"]

    # Verificar primero si ya existen datos
    existing = twitter_col.find_one({"entity": name})
    if existing:
        print(f"Skipping {name} (already exists in DB)")
        continue

    print(f"Searching tweets for: {name}")
    tweets = search_tweets_for_entity(name, max_results=20)
    inserted = store_twitter_data(name, tweets)

    if inserted:
        print("Waiting 15 minutes before next request...")
        time.sleep(900)

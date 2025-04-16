from pymongo import MongoClient
from textblob import TextBlob
import nltk
import unicodedata
from sklearn.preprocessing import MinMaxScaler
from collections import Counter

# MongoDB setup
client = MongoClient("uri")
db = client["media_impact_db"]
players_col = db["players"]
articles_col = db["news_data"]
videos_col = db["youtube_data"]
insights_col = db["player_insights"]

# Download NLTK resources
nltk.download("punkt")

# Safe print
def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii"))

# Positive and negative keyword sets
positive_keywords = {
    "goal", "goals", "assist", "assists", "hat-trick", "clean sheet", "save", "saves",
    "tackle", "tackles", "dribble", "dribbles", "pass", "passes", "interception",
    "decisive", "crucial", "praised", "dominant", "unstoppable", "breakthrough",
    "world-class", "outstanding", "brilliant", "incredible", "captain", "leader",
    "matchwinner", "star", "hero", "highlight", "signed", "respected", "strong",
    "sharp", "accurate", "fast", "vision", "effort", "resilient", "composed",
    "skilled", "clinical", "technical", "legendary", "mentor", "consistency"
}

negative_keywords = {
    "injury", "injured", "suspended", "ban", "fight", "conflict", "controversial",
    "criticism", "criticized", "booed", "racism", "error", "errors", "mistake",
    "mistakes", "red card", "yellow card", "weak", "bad", "poor", "dropped",
    "disappointing", "slow", "sloppy", "unfit", "underperform", "miss", "missed",
    "insecure", "lost", "defeat", "costly", "ineffective", "fragile", "clumsy",
    "struggled", "criticise", "blamed", "penalty missed", "foul", "accused",
    "failed", "trouble", "frustrated", "awkward"
}

# Load player names
players = list(players_col.find())
player_clubs = {p["name"]: p.get("club_name") for p in players}
player_photos = {p["name"]: p.get("photo_base64") for p in players}
player_stats = {p["name"]: {"mention_count": 0, "num_videos": 0, "videos": []} for p in players}


videos = list(videos_col.find())
for video in videos:
    mentioned_in_video = set()
    transcript = video.get("transcript_text", "")
    video_id = video.get("video_id")
    title = video.get("title", "").lower()
    sentences = nltk.sent_tokenize(transcript)

    for sentence in sentences:
        lower_sentence = sentence.lower()
        for name in player_stats:
            name_parts = name.lower().split()
            if name in lower_sentence:
                player_stats[name]["mention_count"] += 1
                mentioned_in_video.add(name)

    for name in player_stats:
        name_parts = name.lower().split()
        if any(part in title for part in name_parts) or name.lower() in title:
            mentioned_in_video.add(name)

    for name in mentioned_in_video:
        player_stats[name]["num_videos"] += 1
        player_stats[name]["videos"].append(str(video_id))

# Analyze articles and combine with YouTube data
all_players = []

for name in player_clubs:
    club = player_clubs[name]
    photo = player_photos[name]
    record = articles_col.find_one({"player": name, "source": "news"})

    if not record or not record.get("articles"):
        continue

    texts = [a["text"] for a in record["articles"] if a.get("text")]
    if not texts:
        continue

    sentiments = [TextBlob(t).sentiment.polarity for t in texts]
    avg_sent = sum(sentiments) / len(sentiments)

    pos_sents, neg_sents = [], []
    for t in texts:
        for s in nltk.sent_tokenize(t):
            p = TextBlob(s).sentiment.polarity
            if p > 0.6:
                pos_sents.append(s.strip())
            elif p < -0.6:
                neg_sents.append(s.strip())

    full_text = " ".join(texts).lower()
    tokens = nltk.word_tokenize(full_text)
    pos_kw = Counter([w for w in tokens if w in positive_keywords])
    neg_kw = Counter([w for w in tokens if w in negative_keywords])

    all_players.append({
        "name": name,
        "club": club,
        "photo_base64": photo,
        "texts": texts,
        "avg_sentiment": avg_sent,
        "count_positive_sentences": len(pos_sents),
        "count_negative_sentences": len(neg_sents),
        "positive_keyword_counts": dict(pos_kw),
        "negative_keyword_counts": dict(neg_kw),
        "strong_positive_sentences": pos_sents,
        "strong_negative_sentences": neg_sents,
        "mention_count": player_stats[name]["mention_count"],
        "num_videos": player_stats[name]["num_videos"],
        "videos": player_stats[name]["videos"]
    })

# Normalize metrics
def normalize_list_1_10(data):
    scaler = MinMaxScaler(feature_range=(1, 10))
    return scaler.fit_transform([[x] for x in data])

sentiments = [p["avg_sentiment"] for p in all_players]
positive_sent_counts = [p["count_positive_sentences"] for p in all_players]
positive_kw_counts = [sum(p["positive_keyword_counts"].values()) for p in all_players]
negative_sent_counts = [p["count_negative_sentences"] for p in all_players]
negative_kw_counts = [sum(p["negative_keyword_counts"].values()) for p in all_players]

S_norm = normalize_list_1_10(sentiments)
FP_norm = normalize_list_1_10(positive_sent_counts)
KP_norm = normalize_list_1_10(positive_kw_counts)
FN_norm = normalize_list_1_10(negative_sent_counts)
KN_norm = normalize_list_1_10(negative_kw_counts)

raw_scores = [
    (S_norm[i][0] + FP_norm[i][0] + KP_norm[i][0] - FN_norm[i][0] - KN_norm[i][0])
    for i in range(len(all_players))
]

impact_scaler = MinMaxScaler(feature_range=(0, 10))
normalized_impact_scores = impact_scaler.fit_transform([[s] for s in raw_scores])

# Save final documents
for i, player in enumerate(all_players):
    doc = {
        "name": player["name"],
        "club": player["club"],
        "photo_base64": player["photo_base64"],
        "num_articles": len(player["texts"]),
        "avg_sentiment_news": round(player["avg_sentiment"], 3),
        "normalized_sentiment_news": round(S_norm[i][0], 2),
        "count_positive_sentences": player["count_positive_sentences"],
        "count_negative_sentences": player["count_negative_sentences"],
        "positive_keyword_counts": player["positive_keyword_counts"],
        "negative_keyword_counts": player["negative_keyword_counts"],
        "strong_positive_sentences": player["strong_positive_sentences"],
        "strong_negative_sentences": player["strong_negative_sentences"],
        "youtube_summary": {
            "mention_count": player["mention_count"],
            "num_videos": player["num_videos"],
            "video_ids": player["videos"]  # list of video _id strings
        },
        "impact_score": round(normalized_impact_scores[i][0], 2)
    }

    insights_col.update_one({"name": player["name"]}, {"$set": doc}, upsert=True)
    safe_print(f" Saved insight for {player['name']} ({player['club']})")

safe_print("\n All player insights updated with YouTube and News data.")

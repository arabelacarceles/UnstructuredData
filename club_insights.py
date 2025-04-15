from pymongo import MongoClient
from textblob import TextBlob
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
from sklearn.preprocessing import MinMaxScaler
import unicodedata

# Descargar recursos necesarios
nltk.download("punkt")

# MongoDB setup
client = MongoClient("mongodb+srv://arabelacarceles:MongoTest123@cluster0.0wssh1x.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["media_impact_db"]
clubs_col = db["clubs"]
tweets_col = db["twitter_data"]
news_col = db["news_data"]
players_col = db["players"]
videos_col = db["youtube_data"]
insights_col = db["club_insights"]

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii"))

def normalize_list(data, feature_range=(1, 10)):
    scaler = MinMaxScaler(feature_range=feature_range)
    return scaler.fit_transform([[x] for x in data])

# Listas de keywords
news_positive = {"victory", "win", "wins", "dominated", "undefeated", "clean sheet", "scored",
    "comeback", "tactical", "resilient", "disciplined", "title contenders", "champions",
    "progress", "secured", "in control", "comfortable", "momentum", "improved", "organized",
    "solid", "effective", "creative", "energetic", "clinical", "determined", "sharp"}

news_negative = {"loss", "lost", "defeat", "conceded", "fragile", "eliminated", "controversy",
    "scandal", "penalty", "missed chances", "errors", "draw", "disorganized",
    "lack of discipline", "injuries", "tensions", "sacked", "booed", "criticism",
    "unstable", "problem", "failure", "collapse", "poor", "ineffective"}

yt_positive = {"goal", "goals", "assist", "assists", "hat-trick", "clean sheet", "save", "saves",
    "dribble", "tackle", "header", "pass", "interception", "counter attack",
    "fast break", "free kick", "long shot", "great run", "world-class", "brilliant",
    "amazing", "fantastic", "unstoppable", "match winner", "man of the match", "celebration"}

yt_negative = {"miss", "missed chance", "penalty miss", "red card", "yellow card", "own goal",
    "injury", "collision", "error", "foul", "dangerous play", "handball", "offside",
    "controversial", "poor clearance", "bad tackle", "blunder", "slip", "mistake",
    "blocked", "slow reaction", "disallowed goal"}

# Preparar diccionarios
clubs = list(clubs_col.find())
club_names = [club["club_name"].lower() for club in clubs]
club_lookup = {club["club_name"].lower(): club["club_name"] for club in clubs}
players = list(players_col.find())
player_to_club = {p["name"].lower(): p["club_name"] for p in players}
player_names = set(player_to_club.keys())

# YOUTUBE STATS
club_stats_yt = {}
for video in videos_col.find():
    transcript = video.get("transcript_text", "")
    sentences = sent_tokenize(transcript)
    mentioned_clubs = set()
    for sentence in sentences:
        s = sentence.lower()
        polarity = TextBlob(sentence).sentiment.polarity
        for club in club_names:
            if club in s:
                club_stats_yt.setdefault(club, {"mention_count": 0, "num_videos": 0, "sentiment_scores": [], "all_text": []})
                club_stats_yt[club]["mention_count"] += 1
                club_stats_yt[club]["sentiment_scores"].append(polarity)
                club_stats_yt[club]["all_text"].append(s)
                mentioned_clubs.add(club)
        for player in player_names:
            if player in s:
                club = player_to_club[player].lower()
                club_stats_yt.setdefault(club, {"mention_count": 0, "num_videos": 0, "sentiment_scores": [], "all_text": []})
                club_stats_yt[club]["mention_count"] += 1
                club_stats_yt[club]["sentiment_scores"].append(polarity)
                club_stats_yt[club]["all_text"].append(s)
                mentioned_clubs.add(club)
    for club in mentioned_clubs:
        club_stats_yt[club]["num_videos"] += 1

# Normalizar sentimientos YT
valid_yt = []
yt_sentiments = []
for club, stats in club_stats_yt.items():
    if stats["mention_count"] > 0:
        yt_sentiments.append(sum(stats["sentiment_scores"]) / len(stats["sentiment_scores"]))
        valid_yt.append(club)
scaler = MinMaxScaler(feature_range=(0, 10))
yt_norm = scaler.fit_transform([[v] for v in yt_sentiments])

# Crear resumen YouTube
yt_summary = {}
for i, club_key in enumerate(valid_yt):
    stats = club_stats_yt[club_key]
    full_text = " ".join(stats["all_text"])
    pos_kw = {k: full_text.count(k) for k in yt_positive if k in full_text}
    neg_kw = {k: full_text.count(k) for k in yt_negative if k in full_text}
    yt_summary[club_lookup[club_key]] = {
        "mention_count": stats["mention_count"],
        "num_videos": stats["num_videos"],
        "avg_sentiment_youtube": round(yt_sentiments[i], 3),
        "normalized_sentiment_youtube": round(yt_norm[i][0], 2),
        "positive_keyword_counts": pos_kw,
        "negative_keyword_counts": neg_kw
    }

# FINAL STATS
all_clubs = []
for club in clubs:
    cname = club["club_name"]
    pnames = [p["name"] for p in players_col.find({"club_name": cname})]
    num_players = len(pnames)

    tw = tweets_col.find_one({"entity": cname, "source": "twitter"})
    nw = news_col.find_one({"club": cname, "source": "news"})

    tweets = [t["content"] for t in tw.get("mentions_data", [])] if tw else []
    articles = [a["text"] for a in nw.get("articles", [])] if nw else []

    if not articles:
        continue

    sent_tw = [TextBlob(t).sentiment.polarity for t in tweets]
    sent_news = [TextBlob(a).sentiment.polarity for a in articles]
    avg_tw = sum(sent_tw) / len(sent_tw) if sent_tw else 0
    avg_news = sum(sent_news) / len(sent_news)

    pos_sents, neg_sents = [], []
    for a in articles:
        for s in sent_tokenize(a):
            p = TextBlob(s).sentiment.polarity
            if p > 0.6: pos_sents.append(s.strip())
            elif p < -0.6: neg_sents.append(s.strip())

    full = " ".join(articles).lower()
    tokens = word_tokenize(full)
    pos_kw = Counter([w for w in tokens if w in news_positive])
    neg_kw = Counter([w for w in tokens if w in news_negative])

    all_clubs.append({
        "club_name": cname,
        "num_players": num_players,
        "player_names": pnames,
        "twitter_summary": {
            "mention_count": tw["mention_count"] if tw else 0,
            "num_tweets": len(tweets)
        },
        "avg_sentiment_twitter": avg_tw,
        "num_articles": len(articles),
        "count_positive_sentences": len(pos_sents),
        "count_negative_sentences": len(neg_sents),
        "positive_keyword_counts": dict(pos_kw),
        "negative_keyword_counts": dict(neg_kw),
        "strong_positive_sentences": pos_sents,
        "strong_negative_sentences": neg_sents,
        "avg_sentiment_news": avg_news,
        "youtube_summary": yt_summary.get(cname, {})
    })

# Normalización final
S = normalize_list([c["avg_sentiment_news"] for c in all_clubs])
FP = normalize_list([c["count_positive_sentences"] for c in all_clubs])
KP = normalize_list([sum(c["positive_keyword_counts"].values()) for c in all_clubs])
FN = normalize_list([c["count_negative_sentences"] for c in all_clubs])
KN = normalize_list([sum(c["negative_keyword_counts"].values()) for c in all_clubs])
TW = normalize_list([c["avg_sentiment_twitter"] for c in all_clubs], feature_range=(0, 10))
RAW = [(S[i][0] + FP[i][0] + KP[i][0] - FN[i][0] - KN[i][0]) for i in range(len(all_clubs))]
IMPACT = normalize_list(RAW, feature_range=(0, 10))

# Save everything
for i, c in enumerate(all_clubs):
    doc = {
        "club_name": c["club_name"],
        "num_players": c["num_players"],
        "player_names": c["player_names"],
        "twitter_summary": c["twitter_summary"],
        "avg_sentiment_twitter": round(c["avg_sentiment_twitter"], 3),
        "normalized_sentiment_twitter": round(TW[i][0], 2),
        "num_articles": c["num_articles"],
        "negative_keyword_counts": c["negative_keyword_counts"],
        "positive_keyword_counts": c["positive_keyword_counts"],
        "strong_negative_sentences": c["strong_negative_sentences"],
        "strong_positive_sentences": c["strong_positive_sentences"],
        "avg_sentiment_news": round(c["avg_sentiment_news"], 3),
        "normalized_sentiment_news": round(S[i][0], 2),
        "youtube_summary": c["youtube_summary"],
        "impact_score": round(IMPACT[i][0], 2)
    }
    insights_col.update_one({"club_name": c["club_name"]}, {"$set": doc}, upsert=True)
    safe_print(f" Saved final insights for {c['club_name']}")

safe_print("\n All club insights updated with Twitter, News, and YouTube data.")

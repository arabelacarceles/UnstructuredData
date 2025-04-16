import streamlit as st
from pymongo import MongoClient
import base64
from PIL import Image
from io import BytesIO

# MongoDB Connection
client = MongoClient(st.secrets["mongo"]["uri"])
db = client["media_impact_db"]
clubs_col = db["club_insights"]
players_col = db["player_insights"]

st.set_page_config(page_title="Premier League Media Impact", layout="wide")
st.title("⚽ Premier League Media Impact Dashboard")
st.markdown("""
This dashboard analyzes the media impact of Premier League clubs and players based on social media, news articles, and YouTube highlights. Select a club to begin:
""")

# Load clubs
documents = list(clubs_col.find())
club_names = sorted([club["club_name"] for club in documents])
selected_club = st.selectbox("Select a Club", club_names)
club_doc = next((club for club in documents if club["club_name"] == selected_club), None)

if club_doc:
    st.subheader(f"{selected_club} Overview")
    
    # Display club logo if exists
    if "logo_base64" in club_doc:
        try:
            logo_data = base64.b64decode(club_doc["logo_base64"])
            image = Image.open(BytesIO(logo_data)).convert("RGB")
            st.image(image, width=120)
        except Exception as e:
            st.warning(f"Could not load logo: {e}")

    # Club insights
    st.markdown("### Club Insights")
    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Players", club_doc.get("num_players", "-"))
    col2.metric("Twitter Score", club_doc.get("normalized_sentiment_twitter", 0), help="Normalized sentiment based on tweets")
    col3.metric("Overall Impact Score", club_doc.get("impact_score", 0), help="Composite media impact score")

    # Top keywords
    st.markdown("### 🔑 Top Mentioned Keywords (News + YouTube)")
    col4, col5 = st.columns(2)
    with col4:
        st.write("**Positive Keywords**")
        st.json(club_doc.get("positive_keyword_counts", {}))
    with col5:
        st.write("**Negative Keywords**")
        st.json(club_doc.get("negative_keyword_counts", {}))

    # Select a player from this club
    st.markdown("---")
    st.markdown("### Select a Player")
    player_docs = list(players_col.find({"club": selected_club}))
    player_names = sorted([p["name"] for p in player_docs])
    selected_player = st.selectbox("Select a Player", player_names)
    player_doc = next((p for p in player_docs if p["name"] == selected_player), None)

    if player_doc:
        st.subheader(f"{selected_player} - Insights")

        # Player image
        if "photo_base64" in player_doc:
            try:
                img_data = base64.b64decode(player_doc["photo_base64"])
                image = Image.open(BytesIO(img_data)).convert("RGB")
                st.image(image, width=100)
            except Exception as e:
                st.warning(f"Could not load player image: {e}")

        st.metric("News Impact Score", player_doc.get("impact_score", 0))
        st.metric("Normalized Sentiment (News)", player_doc.get("normalized_sentiment_news", 0))

        st.markdown("#### 🔑 Player Keywords")
        col6, col7 = st.columns(2)
        with col6:
            st.write("**Positive Keywords**")
            st.json(player_doc.get("positive_keyword_counts", {}))
        with col7:
            st.write("**Negative Keywords**")
            st.json(player_doc.get("negative_keyword_counts", {}))

        if "youtube_summary" in player_doc:
            st.markdown("#### 📺 YouTube Mentions")
            yt = player_doc["youtube_summary"]
            st.write(f"Mentioned in **{yt.get('num_videos', 0)}** videos with **{yt.get('mention_count', 0)}** total mentions.")

import streamlit as st
from pymongo import MongoClient
import base64
from PIL import Image
from io import BytesIO
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# --- MongoDB Connection ---
client = MongoClient(st.secrets["mongo"]["uri"])
db = client["media_impact_db"]
clubs_col = db["clubs"]
club_insights_col = db["club_insights"]
players_col = db["player_insights"]

# --- Page Configuration ---
st.set_page_config(page_title="Premier League Media Impact", layout="wide")
st.markdown("""
    <style>
        .club-header {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-top: 30px;
            margin-bottom: 10px;
        }
        .club-logo-emoji {
            width: 45px;
            height: 45px;
            border-radius: 100%;
            object-fit: cover;
            box-shadow: 0 0 5px rgba(0,0,0,0.15);
        }
        .club-name {
            font-size: 2.8rem;
            font-weight: 900;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .select-style label {
            font-weight: bold;
            font-size: 1.1rem;
        }
        h1 {
            font-family: Arial Black, sans-serif;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# --- Title and Introduction ---
st.markdown("<h1>Premier League Media Impact Dashboard</h1>", unsafe_allow_html=True)
st.markdown("This dashboard analyzes the media impact of Premier League clubs and players based on social media, news articles, and YouTube highlights.")

# --- Club Selector ---
st.markdown('<div class="select-style">Select a Club</div>', unsafe_allow_html=True)
club_docs = list(club_insights_col.find())
club_names = sorted([club["club_name"] for club in club_docs])
selected_club = st.selectbox("", [""] + club_names)

if selected_club:
    # --- Club Header with Logo ---
    club_data = next((c for c in club_docs if c["club_name"] == selected_club), None)
    logo_data = clubs_col.find_one({"club_name": selected_club})

    st.markdown('<div class="club-header">', unsafe_allow_html=True)
    if logo_data and "logo_base64" in logo_data:
        try:
            logo_bytes = base64.b64decode(logo_data["logo_base64"])
            logo_img = Image.open(BytesIO(logo_bytes)).convert("RGBA")
            transparent_background = Image.new("RGBA", logo_img.size, (255, 255, 255, 0))
            transparent_background.paste(logo_img, mask=logo_img.split()[3])
            buffered = BytesIO()
            transparent_background.save(buffered, format="PNG")
            logo_b64 = base64.b64encode(buffered.getvalue()).decode()
            st.markdown(f'<div class="club-name">{selected_club} <img class="club-logo-emoji" src="data:image/png;base64,{logo_b64}"/></div>', unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Could not load logo: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Key Club Metrics ---
    st.subheader("📊 Club Insights")
    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Players", club_data.get("num_players", "-"))
    col2.metric("Twitter Score", club_data.get("normalized_sentiment_twitter", 0), help="Normalized sentiment from tweets")
    col3.metric("Overall Impact Score", club_data.get("impact_score", 0), help="Composite media impact score")

    # --- Keyword Bar Charts ---
    st.subheader("🔑 Top Mentioned Keywords (News + YouTube)")
    positive_keywords = club_data.get("positive_keyword_counts", {})
    negative_keywords = club_data.get("negative_keyword_counts", {})

    df_pos = pd.DataFrame(positive_keywords.items(), columns=["Keyword", "Count"]).sort_values("Count", ascending=True)
    df_neg = pd.DataFrame(negative_keywords.items(), columns=["Keyword", "Count"]).sort_values("Count", ascending=True)

    col4, col5 = st.columns(2)
    with col4:
        st.markdown("**🟢 Positive Keywords**")
        if not df_pos.empty:
            fig_pos = px.bar(df_pos, x="Count", y="Keyword", orientation="h", color_discrete_sequence=["green"])
            fig_pos.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_pos, use_container_width=True)
        else:
            st.write("No positive keywords found.")

    with col5:
        st.markdown("**🔴 Negative Keywords**")
        if not df_neg.empty:
            fig_neg = px.bar(df_neg, x="Count", y="Keyword", orientation="h", color_discrete_sequence=["red"])
            fig_neg.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_neg, use_container_width=True)
        else:
            st.write("No negative keywords found.")

    # --- Word Clouds ---
    st.subheader("☁️ WordCloud of Keywords")
    col_wc1, col_wc2 = st.columns(2)

    with col_wc1:
        st.markdown("**🟢 Positive Keywords Cloud**")
        if not df_pos.empty:
            wc_pos = WordCloud(width=600, height=300, background_color="white", colormap="Greens").generate_from_frequencies(dict(positive_keywords))
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.imshow(wc_pos, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.write("No positive keywords to generate cloud.")

    with col_wc2:
        st.markdown("**🔴 Negative Keywords Cloud**")
        if not df_neg.empty:
            wc_neg = WordCloud(width=600, height=300, background_color="white", colormap="Reds").generate_from_frequencies(dict(negative_keywords))
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.imshow(wc_neg, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.write("No negative keywords to generate cloud.")        

    # --- Comparative Club Scores ---
    st.subheader("📊 Comparative Club Scores")
    all_data = pd.DataFrame(club_docs)

    twitter_sorted = all_data.sort_values("normalized_sentiment_twitter", ascending=False)
    twitter_sorted["bar_color"] = twitter_sorted["club_name"].apply(lambda x: "#636EFA" if x == selected_club else "#CCCCCC")
    fig_sent = px.bar(
        twitter_sorted,
        x="club_name", 
        y="normalized_sentiment_twitter",
        color="bar_color",
        color_discrete_map="identity",
        title="Twitter Score Comparison",
        category_orders={"club_name": twitter_sorted["club_name"].tolist()}
    )
    fig_sent.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_sent, use_container_width=True)

    impact_sorted = all_data.sort_values("impact_score", ascending=False)
    impact_sorted["bar_color"] = impact_sorted["club_name"].apply(lambda x: "#636EFA" if x == selected_club else "#CCCCCC")
    fig_impact = px.bar(
        impact_sorted,
        x="club_name", 
        y="impact_score",
        color="bar_color",
        color_discrete_map="identity",
        title="Overall Impact Score Comparison",
        category_orders={"club_name": impact_sorted["club_name"].tolist()}
    )
    fig_impact.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_impact, use_container_width=True)

    # --- Player Insights ---
    st.markdown("---")
    st.subheader("🎯 Select a Player")
    players = list(players_col.find({"club": selected_club}))
    player_names = sorted([p["name"] for p in players])
    selected_player = st.selectbox("Select a Player", [""] + player_names)

    if selected_player:
        player = next((p for p in players if p["name"] == selected_player), None)
        st.subheader(f"{selected_player} - Insights")

        if player and "photo_base64" in player:
            try:
                img_data = base64.b64decode(player["photo_base64"])
                player_img = Image.open(BytesIO(img_data)).convert("RGBA")
                st.image(player_img, width=120)
            except Exception as e:
                st.warning(f"Could not load player image: {e}")

        st.metric("Overall Impact Score", player.get("impact_score", 0))

        # --- Player Keyword Bar Charts ---
        df_pos_p = pd.DataFrame(player.get("positive_keyword_counts", {}).items(), columns=["Keyword", "Count"]).sort_values("Count", ascending=True)
        df_neg_p = pd.DataFrame(player.get("negative_keyword_counts", {}).items(), columns=["Keyword", "Count"]).sort_values("Count", ascending=True)

        col_bar1, col_bar2 = st.columns(2)
        with col_bar1:
            st.markdown("**🟢 Positive Keywords**")
            if not df_pos_p.empty:
                fig_pos_p = px.bar(df_pos_p, x="Count", y="Keyword", orientation="h", color_discrete_sequence=["green"])
                st.plotly_chart(fig_pos_p, use_container_width=True)
            else:
                st.write("No positive keywords found.")

        with col_bar2:
            st.markdown("**🔴 Negative Keywords**")
            if not df_neg_p.empty:
                fig_neg_p = px.bar(df_neg_p, x="Count", y="Keyword", orientation="h", color_discrete_sequence=["red"])
                st.plotly_chart(fig_neg_p, use_container_width=True)
            else:
                st.write("No negative keywords found.")

        # --- Player Word Clouds ---
        st.subheader("☁️ WordCloud of Player Keywords")
        col_wc_p1, col_wc_p2 = st.columns(2)

        with col_wc_p1:
            st.markdown("**🟢 Positive Keywords Cloud**")
            if not df_pos_p.empty:
                wc_pos_p = WordCloud(width=600, height=300, background_color="white", colormap="Greens").generate_from_frequencies(dict(player.get("positive_keyword_counts", {})))
                fig, ax = plt.subplots(figsize=(6, 3))
                ax.imshow(wc_pos_p, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)

        with col_wc_p2:
            st.markdown("**🔴 Negative Keywords Cloud**")
            if not df_neg_p.empty:
                wc_neg_p = WordCloud(width=600, height=300, background_color="white", colormap="Reds").generate_from_frequencies(dict(player.get("negative_keyword_counts", {})))
                fig, ax = plt.subplots(figsize=(6, 3))
                ax.imshow(wc_neg_p, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)

        # --- Player Impact Comparison (within club) ---
        st.subheader("📈 Impact Score Comparison (Within Club)")
        df_players = pd.DataFrame(players)
        df_players = df_players[df_players["impact_score"].notnull()]
        df_players["bar_color"] = df_players["name"].apply(lambda x: "#636EFA" if x == selected_player else "#CCCCCC")
        player_order = df_players.sort_values("impact_score", ascending=False)["name"].tolist()

        fig_player_impact = px.bar(
            df_players.sort_values("impact_score", ascending=False),
            x="name",
            y="impact_score",
            color="bar_color",
            color_discrete_map="identity",
            category_orders={"name": player_order},
            title="Player Impact Score Comparison"
        )
        fig_player_impact.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_player_impact, use_container_width=True)

        # --- Player Highlight Videos ---
        if "youtube_summary" in player and "video_ids" in player["youtube_summary"]:
            video_ids = player["youtube_summary"]["video_ids"]
            if video_ids:
                st.markdown("#### 🎥 Player's Highlight Videos")

                videos_html = "<div style='display: flex; overflow-x: auto; gap: 30px; padding-bottom: 15px;'>"
                for video_id in video_ids:
                    video_doc = db["youtube_data"].find_one({"video_id": video_id})
                    if video_doc:
                        title = video_doc.get("title", "Untitled")
                        thumbnail_b64 = video_doc.get("thumbnail_base64")
                        video_url = video_doc.get("video_url")

                        if thumbnail_b64 and video_url:
                            videos_html += f"""
                            <div style='min-width: 300px; max-width: 300px;'>
                                <a href='{video_url}' target='_blank' style='text-decoration: none;'>
                                    <img src='data:image/png;base64,{thumbnail_b64}' style='width: 100%; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);' />
                                    <div style='font-weight: 600; margin-top: 8px; color: #333;'>{title}</div>
                                </a>
                            </div>
                            """
                videos_html += "</div>"

                from streamlit.components.v1 import html
                html(videos_html, height=360)
            else:
                st.info("This player has not been mentioned in any YouTube videos.")

# 🏟️ Premier League Media Impact

An interactive data analysis and visualization project focused on evaluating the **media impact** of **Premier League clubs and players** using **social media**, **online news**, and **YouTube highlights**.

🔗 **Live Dashboard**: [https://premierleaguemediaimpact.streamlit.app/](https://premierleaguemediaimpact.streamlit.app/)

---

## 📌 Project Overview

This project is designed to collect, process, and analyze **unstructured data** from multiple online sources to provide insights into how clubs and players are portrayed in media. It supports **decision-makers** in sports management, marketing, and fan engagement by visualizing relevant metrics and media impact indicators.

---

## 🧰 Tech Stack

| Tool               | Role                                                  |
|--------------------|-------------------------------------------------------|
| **MongoDB Atlas**  | NoSQL database to store all structured data          |
| **Python**         | Core language for scraping, ETL, and sentiment analysis |
| **Streamlit**      | UI framework for building the interactive dashboard  |
| **BeautifulSoup4** | HTML parser used for scraping data                   |
| **TextBlob**, **NLTK**, **scikit-learn** | Sentiment analysis and keyword extraction |
| **Plotly**, **WordCloud**, **matplotlib** | Visualizations in the dashboard |
| **GitHub**         | Version control and team collaboration               |
| **Google News**, **YouTube**, **Twitter API** | Data sources               |

---

## 📁 Project Structure

```
├── dashboard.py              # Streamlit interface
├── club_insights.py          # Sentiment analysis and scoring for clubs
├── player_insights.py        # Sentiment analysis and scoring for players
├── clubs.py                  # Scraping club data from Transfermarkt
├── players.py                # Scraping player metadata
├── players_photos.py         # Downloading and encoding player images
├── news.py                   # Scraping and processing Google News articles
├── twitter.py                # Tweet collection from Twitter API
├── youtube.py                # Extracting mentions and transcripts from YouTube
├── token.txt                 # Twitter API credentials
├── clubs_insta.json          # Instagram data (manual entry)
├── requirements.txt          # Python dependencies
```

---

## 🧪 Features

### ✅ Data Collection
- Scraping club and player metadata from Transfermarkt.
- Downloading player profile images in base64 format for embedding in the database.
- Using `GoogleNews` + `newspaper3k` to extract full article texts.
- Extracting tweets via the Twitter API (limited by the free plan).
- Downloading YouTube transcripts from Premier League highlight playlists.

### 🧠 Data Processing
- Sentiment analysis using `TextBlob` and `NLTK`.
- Tokenization and keyword frequency analysis.
- Extraction of strong positive/negative sentences based on polarity thresholds.
- Normalization of all scores (0–10) using `MinMaxScaler`.
- Custom **Impact Score**:
  ```
  Impact = Sentiment + Keyword Positives + Positive Sentences
           - Keyword Negatives - Negative Sentences
  ```

### 📊 Interactive Dashboard
- Comparison of **Twitter sentiment** and **overall Impact Score** between clubs.
- Positive and negative keyword bar charts + wordclouds.
- Player-level insights and comparisons within clubs.
- Embedded **YouTube highlights** (scrollable, clickable thumbnails per player).

---

## 🔐 API Limitations & Workarounds

- **Twitter API** (free tier):
  - 15 requests / 15 minutes and max 100 requests / month.
  - Multiple tokens and only club-level tweet scraping.
- **Google News**:
  - Error 429 (`TooManyRequests`) frequently triggered.
  - Workarounds: delay between requests and VPN location switching.
- **YouTube**:
  - No API used. Scraped transcripts and video metadata manually.

---

## 💾 MongoDB Collections

| Collection         | Description                                      |
|--------------------|--------------------------------------------------|
| `clubs`            | Club name, logo (base64), and Transfermarkt URL |
| `players`          | Player name, age, market value, nationality, etc |
| `news_data`        | Articles per club/player (title, source, date, text) |
| `twitter_data`     | Tweets per club and tweet-level metadata        |
| `youtube_data`     | Transcripts, thumbnails, video IDs and URLs     |
| `club_insights`    | Final cleaned and enriched data per club        |
| `player_insights`  | Final cleaned and enriched data per player      |

---

## ⚙️ How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/your-username/premier-league-media-impact.git
cd premier-league-media-impact

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create Streamlit secrets
# Add a .streamlit/secrets.toml file with:
[mongo]
uri = "your_mongodb_atlas_uri"

# 4. Launch the dashboard
streamlit run dashboard.py
```

---

## 📄 License

This project was developed for educational and academic purposes only. All media content belongs to their respective owners. No commercial usage intended.

---

## ✍️ Authors

Project developed by Master in Business Analytics students at Hult International Business School (2025), as part of the *Unstructured Data & AI for Decision Making* module.

🏟️ Premier League Media Impact

An interactive data analysis and visualization project focused on evaluating the media impact of Premier League clubs and players using social media, online news, and YouTube highlights.

🔗 Live Dashboard: https://premierleaguemediaimpact.streamlit.app/
📌 Project Overview

This project is designed to collect, process, and analyze unstructured data from multiple online sources to provide insights into how clubs and players are portrayed in media. It aims to support decision-makers in sports management, marketing, and fan engagement by providing a clear view of media presence and sentiment.
🧰 Tech Stack
Tool	Role
MongoDB Atlas	NoSQL database to store all structured data
Python	Core programming language for scraping, data cleaning and analysis
Streamlit	Web interface for interactive dashboard
BeautifulSoup4, requests	Web scraping
TextBlob, NLTK, scikit-learn	Sentiment analysis & keyword extraction
Plotly, WordCloud, matplotlib	Visualizations
GitHub	Version control and collaboration
Google News, YouTube, Twitter API	Data sources
📦 Project Structure

├── dashboard.py              # Streamlit app
├── club_insights.py          # Club-level sentiment and impact analysis
├── player_insights.py        # Player-level sentiment and impact analysis
├── clubs.py                  # Scraping and storing club data
├── players.py                # Scraping and storing player data
├── players_photos.py         # Downloading and storing player images
├── news.py                   # Scraping Google News articles
├── twitter.py                # Collecting Twitter data
├── youtube.py                # Extracting YouTube transcripts and mentions
├── token.txt                 # Twitter API credentials
├── clubs_insta.json          # Instagram metrics (manual input)
├── requirements.txt          # Python dependencies

🧪 Features
✅ Data Collection

    Scrapes clubs and players from Transfermarkt.

    Downloads player images in base64 for database storage.

    Fetches news from Google News and full article text using newspaper3k.

    Pulls tweets for each club (limited by Twitter API restrictions).

    Extracts transcripts and metadata from YouTube highlight videos.

🧠 Data Processing

    Cleans and preprocesses text from all sources.

    Calculates sentiment polarity using TextBlob.

    Custom positive/negative keyword dictionaries used to enhance interpretability.

    Computes a custom Impact Score combining multiple indicators:

    Impact = f(sentiment + keyword frequency + strong sentiment phrases)

📊 Dashboard Insights

    Club comparison charts (Twitter sentiment, Impact Score).

    Positive/negative keyword analysis via bar charts and wordclouds.

    Player-level breakdowns (media impact, mentions, keywords).

    Scrollable, clickable YouTube highlights per player.

🔐 API & Rate Limits

    Twitter API: Limited to 15 requests per 15 min with the free tier → scraped only club-level tweets and used multiple accounts.

    Google News: Returned 429 TooManyRequests errors during large-scale scraping → added time.sleep() and VPN rotation to mitigate.

    YouTube: Transcript and video metadata scraped from highlight playlists.

💾 MongoDB Collections
Collection	Description
clubs	Club names, logos (base64), squad URL
players	Player metadata (name, age, position, nationality, photo...)
news_data	News articles from Google News
twitter_data	Tweet content and mentions per club
youtube_data	Transcripts, titles, thumbnails, and URLs
club_insights	Final enriched club analytics
player_insights	Final enriched player analytics
📷 Screenshots

You can include here:

    A screenshot of the full dashboard homepage.

    A sample of the player insights section.

    A preview of wordclouds or highlight videos.

📌 How to Run Locally

# 1. Clone the repo
git clone https://github.com/your-username/premier-league-media-impact.git
cd premier-league-media-impact

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .streamlit/secrets.toml file
[mongo]
uri = "your_mongodb_connection_uri"

# 4. Run the app
streamlit run dashboard.py

📄 License

This project is for educational and academic purposes only. No commercial use intended. All rights to the scraped content belong to their respective owners.

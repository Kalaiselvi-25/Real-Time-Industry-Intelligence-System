import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import time

# Load API key
load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

# Files and folders
data_folder = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(data_folder, exist_ok=True)

merged_file = os.path.join(data_folder, "ai_news_merged.csv")

# Load previously saved articles if merged file exists
if os.path.exists(merged_file):
    merged_df = pd.read_csv(merged_file)
else:
    merged_df = pd.DataFrame()

# Function to fetch AI news 
def fetch_ai_news():
    from_date = "2025-09-15"
    to_date = datetime.today().strftime("%Y-%m-%d")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "artificial intelligence OR AI OR technology",
        "from": from_date,
        "to": to_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 100,
        "apiKey": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("status") != "ok":
        print("Error:", data.get("message"))
        return

    articles = data.get("articles", [])

    if articles:
        df_new = pd.DataFrame(articles)
        global merged_df
        merged_df = pd.concat([merged_df, df_new], ignore_index=True)
        merged_df.to_csv(merged_file, index=False)
        
    else:
        print(f"No articles found. Checked up to {to_date}.")

# Live fetch every 10 minutes 
refresh_interval = 10 * 60  

# First fetch immediately
fetch_ai_news()

# Continuous fetch every 10 minutes
while True:
    print(f"\nWaiting 10 minutes before next fetch...")
    time.sleep(refresh_interval)
    fetch_ai_news()

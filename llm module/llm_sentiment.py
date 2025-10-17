import os
import time
import pandas as pd
import json
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

input_file = os.path.join("data", "ai_news_processed.csv")
output_file = os.path.join("data", "ai_news_sentiment.csv")

df = pd.read_csv(input_file)

df["sentiment_label"] = ""
df["sentiment_score"] = 0.0

REQUESTS_PER_MINUTE = 20
SLEEP_TIME = 60 / REQUESTS_PER_MINUTE

def parse_json_safe(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return {}
    return {}

def get_sentiment(text):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Analyze sentiment and return ONLY JSON in format{{\"label\": \"Positive/Negative/Neutral\", \"score\": float}}:\n\n{text}"
        )
        sentiment = parse_json_safe(response.text)

        label = sentiment.get("label")
        if label not in ["Positive", "Negative", "Neutral"]:
            label = "Neutral"

        score = sentiment.get("score")
        if not isinstance(score, (int, float)):
            score = 0.0

        if label == "Negative":
            score = -abs(score)
        elif label == "Neutral":
            score = 0.0
        else:
            score = abs(score)

        return label, score
    except Exception as e:
        print("Error:", e)
        return "Neutral", 0.0

for i, row in df.iterrows():
    text = row["content"]
    label, score = get_sentiment(text)
    df.at[i, "sentiment_label"] = label
    df.at[i, "sentiment_score"] = score
    print(f"Processed row {i+1}/{len(df)}: {label}, {score}")
    time.sleep(SLEEP_TIME)
     
columns_to_keep = [
    "author",
    "title",
    "description",
    "publishedAt",
    "content",
    "cleaned_content",
    "sentiment_score",
    "sentiment_label"
]
df = df[columns_to_keep]

df.to_csv(output_file, index=False)
print(f"Sentiment analysis completed. Results saved to {output_file}")

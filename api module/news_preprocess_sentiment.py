import os
import pandas as pd
import re
from textblob import TextBlob
from nltk.corpus import stopwords
import nltk

nltk.download('stopwords', quiet=True)
nltk.data.path.append(r"C:\Users\kalai\AppData\Roaming\nltk_data")

# File paths
data_folder = os.path.join(os.path.dirname(__file__), "..", "data")
merged_file = os.path.join(data_folder, "ai_news_merged.csv")
processed_file = os.path.join(data_folder, "ai_news_processed.csv")

# Load dataset
if not os.path.exists(merged_file):
    print(f"Merged dataset not found at {merged_file}")
    exit()

df = pd.read_csv(merged_file)

# Preprocessing
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = [w for w in text.split() if w not in stop_words]
    return ' '.join(words)

# Combine title + description
df['content'] = df['title'].fillna('') + " " + df['description'].fillna('')
df['cleaned_content'] = df['content'].apply(preprocess_text)

# Sentiment Analysis (label + score)
def get_sentiment_and_score(text):
    if not text:
        return pd.Series(["Neutral", 0.0])
    analysis = TextBlob(text)
    score = analysis.sentiment.polarity
    if score > 0.05:
        sentiment = "Positive"
    elif score < -0.05:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
    return pd.Series([sentiment, round(score, 2)])

df[['sentiment', 'sentiment_score']] = df['cleaned_content'].apply(get_sentiment_and_score)

# Keep only the desired columns
columns_to_keep = ['author', 'title', 'description', 'publishedAt', 'content', 'cleaned_content', 'sentiment', 'sentiment_score']
df = df[columns_to_keep]

# Save processed dataset
df.to_csv(processed_file, index=False)

print(f"Processed file saved to: {processed_file}")

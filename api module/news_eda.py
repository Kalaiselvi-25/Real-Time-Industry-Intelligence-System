import os
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import re

# File paths 
data_folder = os.path.join(os.path.dirname(__file__), "..", "data")
processed_file = os.path.join(data_folder, "ai_news_processed.csv")
eda_folder = os.path.join(data_folder, "eda_results")
os.makedirs(eda_folder, exist_ok=True)

# Load processed dataset 
if not os.path.exists(processed_file):
    print(f"Processed da taset not found at {processed_file}")
    exit()

df = pd.read_csv(processed_file)

#  1. Basic Statistics
print("Total articles:", len(df))
print("\nSentiment distribution:")
print(df['sentiment'].value_counts())

#  2. Sentiment Distribution Bar Chart 
sentiment_counts = df['sentiment'].value_counts()
plt.figure(figsize=(6,4))
color_map = {'Positive':'green', 'Negative':'red', 'Neutral':'gray'}
colors = [color_map[sent] for sent in sentiment_counts.index]
sentiment_counts.plot(kind='bar', color=colors)
plt.title("Sentiment Distribution of AI News")
plt.xlabel("Sentiment")
plt.ylabel("Number of Articles")
plt.tight_layout()
plt.savefig(os.path.join(eda_folder, "sentiment_distribution.png"))
plt.show()

#  3. Word Count Bar Chart 
all_text = " ".join(df['cleaned_content'].astype(str))
words = re.findall(r'\b\w+\b', all_text)
word_freq = Counter(words)
top_words = word_freq.most_common(20)  # Top 20 words

# Convert to DataFrame
word_freq_df = pd.DataFrame(top_words, columns=['word', 'count'])
print("\nTop 20 most frequent words:")
print(word_freq_df)

# Plot bar chart
plt.figure(figsize=(10,5))
plt.bar(word_freq_df['word'], word_freq_df['count'], color='skyblue')
plt.xticks(rotation=45, ha='right')
plt.title("Top 20 Most Frequent Words in AI News")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig(os.path.join(eda_folder, "word_count_bar.png"))
plt.show()


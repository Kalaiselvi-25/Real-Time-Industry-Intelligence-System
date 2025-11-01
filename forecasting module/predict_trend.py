import os
import pandas as pd
import requests
from prophet import Prophet
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")

input_file = "data/ai_news_sentiment.csv"
df = pd.read_csv(input_file)
df['publishedAt'] = pd.to_datetime(df['publishedAt'])

daily_sentiment = (
    df.groupby(df['publishedAt'].dt.date)['sentiment_score']
    .mean()
    .reset_index()
    .rename(columns={'publishedAt': 'ds', 'sentiment_score': 'y'})
)

model = Prophet(daily_seasonality=True)
model.fit(daily_sentiment)

FORECAST_DAYS = 7
future_dates = model.make_future_dataframe(periods=FORECAST_DAYS)
forecast = model.predict(future_dates)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()

forecast['trend'] = forecast['yhat'].diff().apply(
    lambda x: "Rising" if x > 0.05 else ("Falling" if x < -0.05 else "Stable")
)

future_forecast = forecast.tail(FORECAST_DAYS).copy()

plt.figure(figsize=(10, 5))
plt.fill_between(
    future_forecast['ds'],
    future_forecast['yhat_lower'],
    future_forecast['yhat_upper'],
    color='skyblue', alpha=0.3, label='Confidence Interval'
)
plt.plot(future_forecast['ds'], future_forecast['yhat'],
         color='black', linewidth=2.5, label='Predicted Trend')
plt.scatter(future_forecast['ds'], future_forecast['yhat'],
            color='black', s=40)

for _, row in future_forecast.iterrows():
    plt.text(row['ds'], row['yhat'] + 0.03,
             f"{row['yhat']:.2f}", ha='center', fontsize=8, color='black')

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.gcf().autofmt_xdate()

plt.title("Sentiment Forecast (Next 7 days)", fontsize=13)
plt.xlabel("Date")
plt.ylabel("Predicted Sentiment Score")
plt.grid(True, linestyle='--', alpha=0.4)
plt.legend(loc='upper left', fontsize=9)
plt.tight_layout()

png_file = "data/ai_sentiment_forecast.png"
plt.savefig(png_file, dpi=300)
plt.show()
plt.close()
print(f" Forecast graph saved as: {png_file}")

output_csv = "data/ai_sentiment_forecast.csv"
future_forecast.to_csv(output_csv, index=False)
print(f"Forecast saved to: {output_csv}")

for _, row in future_forecast.iterrows():
    forecast_date = pd.Timestamp(row['ds']).date()
    predicted = row['yhat']
    trend = row['trend']

    category = (
        "Positive" if predicted > 0.05
        else "Negative" if predicted <-0.05
        else "Neutral"
    )

    message = (
        f"Sentiment Forecast Update\n"
        f"📅 Date: {forecast_date}\n"
        f"📈 Predicted Score: {predicted:.2f} ({category})\n"
        f"📊 Trend: {trend}"
    )

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
        response.raise_for_status()
        print(f"✅ Slack alert sent for {forecast_date} ({trend})")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Failed to send Slack alert for {forecast_date}: {e}")

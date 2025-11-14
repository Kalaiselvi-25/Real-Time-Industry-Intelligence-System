import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from collections import Counter
import re
from prophet import Prophet
import os
import requests
from dotenv import load_dotenv

st.set_page_config(page_title="AI Sentiment Dashboard", layout="wide")
st.title(" AI Sentiment Analysis Dashboard ")

load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Dashboard", "Visualizations", "Trend Forecast"]
)

csv_path = "data/ai_news_sentiment.csv"

if not os.path.exists(csv_path):
    st.error(f"❌ CSV not found at {csv_path}")
    st.stop()

df = pd.read_csv(csv_path)

sentiment_col = "sentiment_label"
score_col = "sentiment_score"
date_col = "publishedAt"
title_col = "title"

df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

if page == "Dashboard":
    st.header("📊 Sentiment Overview")

    total_articles = len(df)
    pos_count = len(df[df[sentiment_col].str.lower() == "positive"])
    neg_count = len(df[df[sentiment_col].str.lower() == "negative"])
    neu_count = len(df[df[sentiment_col].str.lower() == "neutral"])
    avg_score = df[score_col].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📰 Total Articles", total_articles)
    c2.metric("😊 Positive", pos_count)
    c3.metric("😞 Negative", neg_count)
    c4.metric("📊 Avg Sentiment Score", f"{avg_score:.2f}")

    st.divider()
    st.subheader("🆕 Latest 10 Articles")

    st.dataframe(df[[title_col, sentiment_col, score_col]].tail(10).sort_index(ascending=False))

elif page == "Visualizations":
    st.header("📈 Sentiment Visualizations")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Sentiment Distribution")
        fig_pie = px.pie(df, names=sentiment_col, hole=0.3)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("#### ☁️ Word Cloud")
        text_data = " ".join(df[title_col].astype(str))
        wc = WordCloud(width=800, height=400, background_color="black").generate(text_data)
        st.image(wc.to_array(), use_container_width=True)

    st.divider()
    st.markdown("#### 🔠 Top Frequent Words")
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text_data.lower())
    common_words = Counter(words).most_common(15)
    top_df = pd.DataFrame(common_words, columns=["Word", "Count"])
    fig_bar = px.bar(top_df, x="Word", y="Count", title="Most Common Words in Titles")
    st.plotly_chart(fig_bar, use_container_width=True)

elif page == "Trend Forecast":
    st.header("🔮 Sentiment Forecast (Next 14 Days - Every 3 Days)")

    daily_sentiment = (
        df.groupby(df[date_col].dt.date)[score_col]
        .mean()
        .reset_index()
        .rename(columns={date_col: "ds", score_col: "y"})
    )

    model = Prophet(daily_seasonality=True)
    model.fit(daily_sentiment)

    last_date = pd.Timestamp(daily_sentiment["ds"].max())
    future_dates = pd.DataFrame({
        "ds": [last_date + pd.Timedelta(days=i) for i in range(2, 21, 3)]
    })

    forecast = model.predict(future_dates)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    forecast["trend"] = forecast["yhat"].diff().apply(
        lambda x: "🔼 Rising" if x > 0.05 else ("🔽 Falling" if x < -0.05 else "⏺ Stable")
    )
    forecast["category"] = forecast["yhat"].apply(
        lambda y: "Positive" if y > 0.05 else "Negative" if y < -0.05 else "Neutral"
    )

    st.markdown("#### 📅 Forecasted Sentiment (Every 3 Days)")
    st.dataframe(forecast.style.format({"yhat": "{:.2f}"}))

    # Visualization
    st.markdown("#### 📈 Forecast Visualization")
    fig_forecast = px.line(
        forecast, x="ds", y="yhat", markers=True,
        title="Predicted Sentiment Trend (3-Day Intervals)",
        labels={"ds": "Date", "yhat": "Predicted Sentiment Score"},
        color_discrete_sequence=["#00CC96"]
    )

    fig_forecast.add_scatter(
        x=forecast["ds"], y=forecast["yhat_upper"], mode="lines",
        name="Upper Bound", line=dict(width=1, dash="dot", color="lightgray")
    )
    fig_forecast.add_scatter(
        x=forecast["ds"], y=forecast["yhat_lower"], mode="lines",
        name="Lower Bound", line=dict(width=1, dash="dot", color="lightgray")
    )

    st.plotly_chart(fig_forecast, use_container_width=True)

    if SLACK_WEBHOOK_URL:
        if "alerts_sent" not in st.session_state:
            st.session_state.alerts_sent = False

        if not st.session_state.alerts_sent:
            st.success("✅ Slack Webhook Detected — Sending Forecast Alerts (first time only)...")

            for _, row in forecast.iterrows():
                forecast_date = pd.Timestamp(row["ds"]).date()
                predicted = row["yhat"]
                trend = row["trend"]
                category = row["category"]

                message = (
                    f"*Sentiment Forecast Update*\n"
                    f"📅 *Date:* {forecast_date}\n"
                    f"📈 *Predicted Score:* {predicted:.2f} ({category})\n"
                    f"📊 *Trend:* {trend}"
                )

                try:
                    response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
                    if response.status_code == 200:
                        st.write(f"✅ Slack alert sent for {forecast_date} ({trend})")
                    else:
                        st.warning(f"⚠️ Slack alert failed for {forecast_date} ({response.status_code})")
                except Exception as e:
                    st.error(f"❌ Slack error: {e}")
            st.session_state.alerts_sent = True
        else:
            st.info("💬 Slack alerts already sent this session. (Reload app to send again)")
    else:
        st.warning("⚠️ No Slack webhook URL found. Add it to your `.env` file.")
  


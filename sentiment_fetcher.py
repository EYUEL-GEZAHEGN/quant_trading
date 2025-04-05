from ntscraper import Nitter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import time

scraper = Nitter(log_level=1, skip_instance_check=False)
analyzer = SentimentIntensityAnalyzer()

def fetch_tweets(query, count=100):
    result = scraper.get_tweets(query, mode='hashtag', language='en', number=count)
    return result.get("tweets", []) if 'tweets' in result else []

def analyze_sentiment(tweets):
    rows = []
    for tweet in tweets:
        user = tweet.get("user", {})
        stats = tweet.get("stats", {})
        text = tweet['text']
        score = analyzer.polarity_scores(text)

        rows.append({
            "username": user.get("username", ""),
            "content": text,
            "date": tweet.get("date", ""),
            "compound": score["compound"],
            "pos": score["pos"],
            "neu": score["neu"],
            "neg": score["neg"],
            "likes": stats.get("likes", 0),
            "retweets": stats.get("retweets", 0),
            "comments": stats.get("comments", 0),
            "quotes": stats.get("quotes", 0),
        })
    return pd.DataFrame(rows)

def get_sentiment_score_for(ticker, count=100):
    tweets = fetch_tweets(f"${ticker}", count)
    if not tweets:
        return 0, pd.DataFrame()

    df = analyze_sentiment(tweets)
    avg_score = df['compound'].mean()
    return avg_score, df

# ✅ Run for testing
if __name__ == "__main__":
    ticker = "AAPL"  # or "TSLA", "NVDA", etc.
    score, df = get_sentiment_score_for(ticker, count=50)

    print(f"\n📈 Sentiment Score for ${ticker}: {score:.4f}")
    print("\n🧾 Sample Tweets + Scores:")
    print(df[['date', 'compound', 'content']].head(5))

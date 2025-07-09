import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import matplotlib.font_manager as fm

df = pd.read_csv("cleaned_comments.csv", encoding="utf-8-sig")

# published_at 컬럼을 datetime으로
df["published_at"] = pd.to_datetime(df["published_at"])
df["date"] = df["published_at"].dt.date
sentiment_counts = df["sentiment"].value_counts()

colors = ['skyblue', 'lightcoral', 'lightgray']
plt.figure(figsize=(6, 6))
plt.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', colors=colors)
plt.title("감정 비율 파이차트")
plt.tight_layout()
plt.show()

time_sentiment = df.groupby(["date", "sentiment"]).size().unstack().fillna(0)

plt.figure(figsize=(10, 5))
for col in time_sentiment.columns:
    plt.plot(time_sentiment.index, time_sentiment[col], label=col)

plt.title("시간별 감정 변화")
plt.xlabel("날짜")
plt.ylabel("댓글 수")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

text_data = " ".join(df["cleaned"].astype(str))  # cleaned 컬럼 사용

font_path = "C:/Windows/Fonts/malgun.ttf"  # 한글폰트 경로

wordcloud = WordCloud(font_path=font_path, background_color="white", width=800, height=400).generate(text_data)

plt.figure(figsize=(12, 6))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("댓글 워드클라우드")
plt.tight_layout()
plt.show()

df.to_csv("cleaned_comments_with_graph.csv", index=False, encoding="utf-8-sig")

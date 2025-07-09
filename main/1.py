import pandas as pd
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from konlpy.tag import Okt
import matplotlib.font_manager as fm


#  감정 분석 함수
def analyze_sentiment(text):
    pos = sum(word in text for word in positive_words)
    neg = sum(word in text for word in negative_words)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    else:
        return "neutral"

df["sentiment_pred"] = df["clean_final"].apply(analyze_sentiment)

# 감정 비율 파이차트
sentiment_counts = df["sentiment_pred"].value_counts()

colors = ['skyblue', 'lightcoral', 'lightgray']
plt.figure(figsize=(6, 6))
plt.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', colors=colors)
plt.title("감정 비율 파이차트")
plt.tight_layout()
plt.show()

# 시간 순 감정 변화 선그래프
df_time = df.copy()
df_time["date"] = df_time["published_at"].dt.date
time_sentiment = df_time.groupby(["date", "sentiment_pred"]).size().unstack().fillna(0)

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

# 7. 워드클라우드 (전체 clean_final 텍스트 기반)
text_data = " ".join(df["clean_final"])

# 시스템에 있는 한글 폰트 경로 지정 (Windows 기준)
font_path = "C:/Windows/Fonts/malgun.ttf"

wordcloud = WordCloud(font_path=font_path, background_color="white", width=800, height=400).generate(text_data)

plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("워드클라우드")
plt.tight_layout()
plt.show()

# 최종 저장
df.to_csv("youtube_comments_final_with_sentiment.csv", index=False)

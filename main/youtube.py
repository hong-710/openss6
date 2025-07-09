import pandas as pd
import re
import emoji
from googleapiclient.discovery import build
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs

from transformers import pipeline
import torch

# -----------------------
# 1. API 키
# -----------------------
API_KEY = 'AIzaSyDpAjP_VVGIVQEfEpuS_GDV-VlvKWzyaMA'  # 꼭 본인 걸로!

# -----------------------
# 2. video_id 추출 함수
# -----------------------
def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    elif 'youtube.com' in parsed_url.hostname:
        query = parse_qs(parsed_url.query)
        return query.get('v', [None])[0]
    else:
        return None

# -----------------------
# 3. 댓글 수집 함수
# -----------------------
def get_comments(video_id, max_comments=500):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    comments = []
    next_page_token = None

    while len(comments) < max_comments:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token,
            textFormat="plainText"
        )
        response = request.execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'text': comment['textDisplay'],
                'published_at': comment['publishedAt']
            })

        if 'nextPageToken' in response:
            next_page_token = response['nextPageToken']
        else:
            break

    return pd.DataFrame(comments)

# -----------------------
# 4. 불용어 로드 & 전처리
# -----------------------
# -----------------------
# 4. 전처리 함수
# -----------------------
def load_stopwords(filepath):
    return pd.read_csv(filepath, header=None)[0].tolist()

def clean_text(text, stopwords):
    text = emoji.replace_emoji(text, replace='')
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.lower()
    words = [word for word in text.split() if word not in stopwords]
    return ' '.join(words)

# -----------------------
# 5. 은어 사전 로드
# -----------------------
slang_df = pd.read_csv("slang_dictionary_v3.csv", encoding="utf-8-sig")
slang_df.columns = slang_df.columns.str.strip()  # 혹시 공백 있으면 제거
slang_dict = dict(zip(slang_df['단어'], slang_df['감정']))

# -----------------------
# 6. 감정분석 파이프라인 준비
# -----------------------
sentiment_pipeline = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# -----------------------
# 7. 감정 분류 함수
# -----------------------
def classify_sentiment(text):
    # 은어 사전 먼저 확인
    for slang_word, sentiment in slang_dict.items():
        if slang_word in text:
            return sentiment

    # 없으면 transformers 모델로 예측
    try:
        result = sentiment_pipeline(text[:200])[0]  # 너무 긴 문장은 앞부분만
        label = result['label']
    except:
        return 'neutral'  # 예외 시 중립 처리

    # 레이블 단순화
    if '5' in label or '4' in label:
        return 'positive'
    elif '1' in label or '2' in label:
        return 'negative'
    else:
        return 'neutral'

# -----------------------
# 8. 메인 실행
# -----------------------
if __name__ == "__main__":
    tqdm.pandas()

    video_url = input("유튜브 영상 URL을 입력하세요: ")
    video_id = extract_video_id(video_url)

    if not video_id:
        print("❌ 올바르지 않은 유튜브 링크입니다.")
        exit()

    print(f"✅ video_id 추출 성공: {video_id}")
    print("📥 댓글 수집 중...")

    df = get_comments(video_id)

    if df.empty:
        print("❌ 댓글이 없거나 수집에 실패했습니다.")
        exit()

    df.to_csv("comments.csv", index=False, encoding='utf-8-sig')
    print("✅ 댓글 수집 완료! comments.csv 저장됨")

    print("🔍 stopwords.csv 로 불용어 목록 불러오는 중...")
    stopwords = load_stopwords("stopwords.csv")

    print("🧹 전처리 중...")
    df['cleaned'] = df['text'].progress_apply(lambda x: clean_text(x, stopwords))

    print("💬 감정 분류 중...")
    df['sentiment'] = df['cleaned'].progress_apply(classify_sentiment)

    df.to_csv("cleaned_comments.csv", index=False, encoding='utf-8-sig')
    print("✅ 전처리+감정분석 완료! cleaned_comments.csv 저장됨")



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



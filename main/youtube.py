import pandas as pd
import re
import emoji
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from googleapiclient.discovery import build
from tqdm.auto import tqdm
from urllib.parse import urlparse, parse_qs
from wordcloud import WordCloud
from konlpy.tag import Okt

# -----------------------
# 1. API 키 입력
# -----------------------
API_KEY = 'AIzaSyABwwARZN_kd22JuDxyHcRySU1FCm3zdCY'

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
# 4. 전처리 함수
# -----------------------
def load_stopwords(filepath):
    return pd.read_csv(filepath, header=None)[0].tolist()

okt = Okt()

def clean_text(text, stopwords, okt):
    text = emoji.replace_emoji(text, replace='')  # 이모지 제거
    text = re.sub(r'[a-zA-Z]+', '', text)    # 영어 제거
    text = re.sub(r'[^ㄱ-ㅎㅏ-ㅣ가-힣0-9\s]', '', text)    # 특수문자 제거 (한글, 숫자, 공백만 남기기)
    text = re.sub(r'\s+', ' ', text).strip()    # 공백 여러개 -> 하나로, 앞뒤 공백 제거
    morphs_pos = okt.pos(text, norm=True, stem=True)    # 형태소 분석 후 품사 태깅
    remove_pos = ['Josa', 'Eomi', 'Punctuation', 'Foreign', 'Alpha', 'Suffix', 'VerbPrefix', 'Conjunction', 'Exclamation']    # 조사, 접속사, 감탄사, 불용어 등 제외할 품사 리스트
    words = [word for word, pos in morphs_pos 
             if pos not in remove_pos and word not in stopwords and len(word) > 1]    # 불용어 + 형태소 기준 제거
    return ' '.join(words)

# -----------------------
# 5. 감정 분석 함수
# -----------------------
# 간단한 긍/부정 단어 리스트 예시

def load_word_list(filepath):
    return pd.read_csv(filepath, header=None)[0].tolist()

positive_words = load_word_list("positive.csv")
negative_words = load_word_list("negative.csv")

def analyze_sentiment(text):
    pos = sum(word in text for word in positive_words)
    neg = sum(word in text for word in negative_words)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    else:
        return "neutral"

# -----------------------
# 6. 모델 실행 및 시각화
# -----------------------

def run_analysis(video_url):
    from konlpy.tag import Okt
    tqdm.pandas()

    video_id = extract_video_id(video_url)
    if not video_id:
        return "❌ 올바르지 않은 유튜브 링크입니다."

    df = get_comments(video_id)
    if df.empty:
        return "❌ 댓글이 없거나 수집에 실패했습니다."

    df['published_at'] = pd.to_datetime(df['published_at'])
    stopwords = load_stopwords("stopwords.csv")

    okt = Okt()
    df['cleaned'] = df['text'].progress_apply(lambda x: clean_text(x, stopwords, okt))
    df["sentiment_pred"] = df["cleaned"].apply(analyze_sentiment)
    df['date'] = df['published_at'].dt.date

    # 시각화 1: 파이차트
    sentiment_counts = df["sentiment_pred"].value_counts()
    colors = ['skyblue', 'lightcoral', 'lightgray']
    plt.figure(figsize=(6, 6))
    plt.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', colors=colors)
    plt.title("Pie chart")
    plt.tight_layout()
    plt.savefig("main/static/img/result.png")
    plt.close()

    # 시각화 2: 선그래프
    time_sentiment = df.groupby(["date", "sentiment_pred"]).size().unstack().fillna(0)
    plt.figure(figsize=(10, 5))
    for col in time_sentiment.columns:
        plt.plot(time_sentiment.index, time_sentiment[col], label=col)
    plt.title("Emotional changes over time")
    plt.xlabel("date")
    plt.ylabel("comments count")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("main/static/img/timeseries.png")
    plt.close()

    # 시각화 3: 워드클라우드
    font_path = "C:/Windows/Fonts/malgun.ttf"
    text_data = " ".join(df["cleaned"])
    wordcloud = WordCloud(font_path=font_path, background_color="white", width=800, height=400).generate(text_data)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title("Word Cloud")
    plt.tight_layout()
    plt.savefig("main/static/img/wordcloud.png")
    plt.close()

    # 결과 리턴
    return f"""분석 완료!
- 총 댓글 수: {len(df)}개
- 긍정: {sentiment_counts.get('positive', 0)}개
- 부정: {sentiment_counts.get('negative', 0)}개
- 중립: {sentiment_counts.get('neutral', 0)}개"""

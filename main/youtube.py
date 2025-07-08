import pandas as pd
import re
import emoji
from googleapiclient.discovery import build
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs


# -----------------------
# 1. API 키 입력
# -----------------------
API_KEY = 'AIzaSyDEa7nG4YJuOyMyNxr4wcv47FyI0GlpUio'  # 발급 받은 키 넣기! 반드시 수정!


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

def clean_text(text, stopwords):
    text = emoji.replace_emoji(text, replace='')              # 이모지 제거
    text = re.sub(r'[^\w\s]', '', text)                       # 특수문자 제거
    text = re.sub(r'\s+', ' ', text)                          # 공백 정리
    text = text.lower()                                       # 소문자화
    words = [word for word in text.split() if word not in stopwords]
    return ' '.join(words)

# -----------------------
# 5. 메인 실행
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

    df.to_csv("cleaned_comments.csv", index=False, encoding='utf-8-sig')
    print("✅ 전처리 완료! cleaned_comments.csv 저장됨")
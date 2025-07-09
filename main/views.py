# views.py

# 이미 있는 import
from django.shortcuts import render
from django.http import JsonResponse
import subprocess

# ✅ NEW: 시각화에 필요한 추가 import
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import io
import base64

# 기존 함수들
def home(request):
    return render(request, 'main/home.html')

def analyze(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')

        subprocess.run(
            ['python', 'main/youtube.py', video_url],
            capture_output=True,
            text=True
        )

        # ✅ 분석 끝나면 결과 페이지로 이동하도록 리디렉트
        from django.shortcuts import redirect
        return redirect('result')  # urls.py에 name='result'로 연결되어 있어야 함

    return render(request, 'main/home.html')


# ✅ 새로 추가할 결과 뷰 함수!
def result_view(request):
    df = pd.read_csv('main/cleaned_comments.csv')  # 경로 맞춰주세요!

    if df.empty:
        return render(request, 'main/result.html', {'error': '❌ 댓글 없음!'})

    sentiment_counts = df['sentiment'].value_counts().to_dict()

    # 워드클라우드
    text = ' '.join(df['cleaned'].dropna())
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    img = io.BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    wordcloud_base64 = base64.b64encode(img.getvalue()).decode()

    # 시간별 감정 추이
    df['published_at'] = pd.to_datetime(df['published_at'])
    df['date'] = df['published_at'].dt.date
    time_sentiment = df.groupby(['date', 'sentiment']).size().unstack(fill_value=0).reset_index()

    context = {
        'sentiment_counts': sentiment_counts,
        'wordcloud_base64': wordcloud_base64,
        'time_sentiment': time_sentiment.to_dict(orient='list'),
    }

    return render(request, 'main/result.html', context)

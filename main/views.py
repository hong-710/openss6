from django.shortcuts import render
from django.http import JsonResponse
import subprocess

def home(request):
    return render(request, 'main/home.html')  # 위의 템플릿 이름과 일치

def analyze(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')

        subprocess.run(
            ['python', 'main/youtube.py', video_url],
            capture_output=True,
            text=True
        )

        return JsonResponse({
            'output': f"분석 완료: {video_url}"
        })

    return render(request, 'main/home.html')  # GET 요청 시 홈으로
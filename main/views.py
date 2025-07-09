from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .youtube import run_analysis  # ✅ run_analysis 함수 가져오기
from django.shortcuts import render

def index(request):
    return render(request, 'main/home.html')

@csrf_exempt
def analyze(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')

        # 바로 함수 호출
        output_text = run_analysis(video_url)

        return JsonResponse({
            'output': output_text,
            'result_img': '/static/img/result.png',
            'timeseries_img': '/static/img/timeseries.png',
            'wordcloud_img': '/static/img/wordcloud.png',
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

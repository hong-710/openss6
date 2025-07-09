# main/urls.py

from django.urls import path
from .views import home, analyze, result_view

urlpatterns = [
    path('', home, name='home'),          # 기본 홈 페이지
    path('analyze/', analyze, name='analyze'),  # 분석 요청 POST
    path('result/', result_view, name='result'),  # 분석 결과 페이지
]

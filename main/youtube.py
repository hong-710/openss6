import sys

def dummy_sentiment_analysis(url):
    return f"링크 '{url}' 에 대한 감정 분석 완료!"

if __name__ == "__main__":
    input_url = sys.argv[1]
    print(dummy_sentiment_analysis(input_url))
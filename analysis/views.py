from django.shortcuts import render
from django.http import JsonResponse
from .utils import load_data, preprocess_reviews, calculate_tfidf
from .models import Review
import json

def analysis(request):
    print('aaa')
    try:
        if request.method == 'POST':
            
            selected_texts = request.POST.get('selected_texts')
            selected_groups = selected_texts.split(',')  # 문자열을 리스트로 변환
            print("Selected groups:", selected_groups)

            # 수정된 데이터 로드 함수 호출
            data = load_data()
            data.head(1)
            data = preprocess_reviews(data)
            data.head(1)
            tfidf_df = calculate_tfidf(data)
            data.head(1)

            # tfidf_df 생성 직후에 열 목록을 출력
            print("Columns in tfidf_df:", tfidf_df.columns.tolist())

            comb_name = '_'.join(selected_groups)
            print(f"comb_name: {comb_name}")

            # comb_name 열 기준으로 상위 3개 타이틀 추출
            top_titles = tfidf_df.sort_values(by=comb_name, ascending=False).head(3).index.tolist()

            top_reviews = []
            keyword_scores = {}

            # 각 title에 대해 selected_groups의 점수 계산
            for title in top_titles:
                scores = {}
                for group in selected_groups:
                    if group in tfidf_df.columns:
                        print(f"Accessing tfidf_df[{title}][{group}]")
                        scores[group] = tfidf_df.loc[title, group]
                    else:
                        print(f"Group '{group}' not found in tfidf_df columns")
                        scores[group] = 0  # 기본값 설정
                keyword_scores[title] = scores

                # CSV 파일에서 상위 타이틀과 연결된 리뷰 추출
                title_reviews = data[data['title2'] == title].sort_values(by='empathy', ascending=False).head(3)
                review_list = []
                for _, review in title_reviews.iterrows():
                    review_list.append({
                        'title': review['title'],
                        'review': review['review'],
                        'empathy': review['empathy'],
                        'url': review['url']
                    })
                top_reviews.append({'title': title, 'reviews': review_list})

            return render(request, 'analysis/analysis.html', {
                'top_reviews': top_reviews,
                'selected_groups': selected_groups,
                'keyword_scores': keyword_scores
            })

    except Exception as e:
        print(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)
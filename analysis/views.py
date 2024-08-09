from django.shortcuts import render
from django.http import JsonResponse
from .utils import load_data, preprocess_reviews, calculate_tfidf
from .models import Review
import json

def analysis(request):
    if request.method == 'POST':
        selected_texts = request.POST.get('selected_texts')
        selected_groups = selected_texts.split(',')  # 문자열을 리스트로 변환
        print(selected_groups)
        
        selected_groups = request.POST.getlist('selected_groups')

        if len(selected_groups) != 3:
            return render(request, 'analysis/analysis.html', {'error': '3개의 그룹을 선택해야 합니다.'})

        data = load_data()
        data = preprocess_reviews(data)
        tfidf_df = calculate_tfidf(data)

        comb_name = '_'.join(selected_groups)
        top_titles = tfidf_df.sort_values(by=comb_name, ascending=False).head(3).index.tolist()

        top_reviews = []
        keyword_scores = {group: tfidf_df.loc[group, comb_name] for group in selected_groups}
        
        for title in top_titles:
            reviews = Review.objects.filter(title2=title).order_by('-empathy')[:3]
            review_list = []
            for review in reviews:
                review_list.append({
                    'title': review.title,
                    'review': review.review,
                    'empathy': review.empathy,
                    'url': review.url
                })
            top_reviews.append({'title': title, 'reviews': review_list})
        return render(request, 'analysis/analysis.html', {'top_reviews': top_reviews, 'selected_groups': selected_groups, 'keyword_scores': keyword_scores})

        
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

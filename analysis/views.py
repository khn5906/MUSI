from django.shortcuts import render
from django.http import JsonResponse
from analysis.utils import load_data, preprocess_reviews, calculate_tfidf
from analysis.models import Review
import json

# Create your views here.
def analysis(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        selected_groups = body.get('selected_groups', [])

        if len(selected_groups) != 3:
            return JsonResponse({'error': '3개의 그룹을 선택해야 합니다.'}, status=400)

        data = load_data()
        data = preprocess_reviews(data)
        tfidf_df = calculate_tfidf(data)

        comb_name = '_'.join(selected_groups)
        top_titles = tfidf_df.sort_values(by=comb_name, ascending=False).head(3).index.tolist()

        top_reviews = []
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

        return JsonResponse({'status': 'success', 'top_reviews': top_reviews})
    return JsonResponse({'error': 'Invalid request method.'}, status=405);

def visualization(request):
    return render(request, 'analysis/visualization.html');

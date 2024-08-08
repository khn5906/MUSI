from django.shortcuts import render, redirect
from django.http import JsonResponse
from .utils import load_data, preprocess_reviews, calculate_tfidf
from .models import Review
import json

def save_selected_keywords(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        selected_groups = body.get('selected_groups', [])

        if len(selected_groups) != 3:
            return JsonResponse({'error': '3개의 그룹을 선택해야 합니다.'}, status=400)

        request.session['selected_groups'] = selected_groups
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def analysis(request):
    selected_groups = request.session.get('selected_groups', [])

    if not selected_groups:
        return render(request, 'analysis.html', {'error': 'No selected groups found.'})

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

    return render(request, 'analysis.html', {
        'recommended_titles': top_titles,
        'top_reviews': top_reviews,
        'selected_groups': selected_groups
    })

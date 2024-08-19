from django.shortcuts import render
from django.http import JsonResponse
from .utils import load_data, generate_radar_chart, process_user_input
import pandas as pd
from rapidfuzz import process
import time
from datetime import datetime, timedelta

current_date = datetime.now().strftime('%Y%m%d')

def analysis(request):
    try:
        if request.method == 'GET':
            return render(request, "analysis/analysis_index.html");

        elif request.method == 'POST':
            
            selected_texts = request.POST.get('selected_texts')
            selected_groups = selected_texts.split(',')  # 문자열을 리스트로 변환

            # 데이터 로드 및 필요한 전처리 작업
            data = load_data()
            score_df = pd.read_csv('keyword_score.csv', index_col='title')
            all_detail_list_df = pd.read_csv(f'myweb/data/data_{current_date}/all_detail_list_{current_date}.csv')  # PRFID를 포함한 데이터

            comb_name = '_'.join(selected_groups)
            top_titles = score_df.sort_values(by=comb_name, ascending=False).head(3).index.tolist()

            top_reviews = []
            keyword_scores = {}
            reservation_urls = {}

            for title in top_titles:
                scores = {}
                for group in selected_groups:
                    scores[group] = score_df.loc[title, group] if group in score_df.columns else 0
                keyword_scores[title] = scores

                # # all_detail_list_df에서 PRFID 추출
                # matching_row = all_detail_list_df[all_detail_list_df['PRFNM'].str.contains(title)]
                # print('matching_row : ', matching_row)
                # if not matching_row.empty:
                #     prfid = matching_row.iloc[0]['PRFID']
                #     reservation_urls[title] = f"/reservation/{prfid}"
                # else:
                #     reservation_urls[title] = None
                # all_detail_list_df에서 PRFID 추출

                matching_row = all_detail_list_df[all_detail_list_df['PRFNM'] == title]

                if not matching_row.empty:
                    # 정확히 일치하는 경우
                    prfid = matching_row.iloc[0]['PRFID']
                    reservation_urls[title] = f"/reservation/{prfid}"
                else:
                    # title과 PRFNM 중 하나가 다른 하나를 포함하는 경우
                    contains_row = all_detail_list_df[all_detail_list_df['PRFNM'].str.contains(title) | all_detail_list_df['PRFNM'].apply(lambda x: title in x)]
                    
                    if not contains_row.empty:
                        # 포함되는 경우 중 첫 번째 항목 선택
                        prfid = contains_row.iloc[0]['PRFID']
                        reservation_urls[title] = f"/reservation/{prfid}"
                    else:
                        # 정확히 일치하지 않는 경우 유사도 계산
                        prfnms = all_detail_list_df['PRFNM'].tolist()
                        match, score, idx = process.extractOne(title, prfnms)

                        if score > 80:  # 유사도 점수가 80보다 클 때만 진행 (1~100점)
                            prfid = all_detail_list_df.iloc[idx]['PRFID']
                            reservation_urls[title] = f"/reservation/{prfid}"
                            print(idx)
                        else:
                            reservation_urls[title] = None
                        
                title_reviews = data[data['title2'] == title].sort_values(by=['empathy', 'star'], ascending=[False, False]).head(3)
                
                review_list = []
                for _, review in title_reviews.iterrows():
                    review_list.append({
                        'title': review['title'],
                        'review': review['review'],
                        'empathy': int(review['empathy']),
                        'star': int(review['star']),
                        'url': review['url']
                    })
                top_reviews.append({'title': title, 'reviews': review_list})
            print('reservation_urls : ', reservation_urls)
            # 여기에서 top_reviews에 keyword_scores와 reservation_urls 병합
            for item in top_reviews:
                title = item['title']
                labels = list(keyword_scores[title].keys())  # 키워드 그룹 이름들
                values = list(keyword_scores[title].values())  # 해당 타이틀의 점수들
                item['keyword_scores'] = keyword_scores.get(title, {})
                item['reservation_url'] = reservation_urls.get(title)
                item['radar_chart'] = generate_radar_chart(title, labels, values)

            return render(request, 'analysis/analysis.html', {
                'top_reviews': top_reviews,
                'selected_groups': selected_groups,
            })

    except Exception as e:
        print(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def analysis_review(request):
    # CSV 파일 로드
    df = pd.read_csv('review_data.csv')  # 실제 경로로 수정

    # 중복되지 않는 title2 값 추출
    titles = df['title2'].unique()
    
    content={
        'titles': titles,
    }
    return render(request, 'analysis/analysis2_index.html', content)

def process_input(request):
    if request.method == 'POST':
        # 사용자가 입력한 데이터 가져오기
        title = request.POST.get('title')
        rating = float(request.POST.get('rating'))
        review = request.POST.get('review')
        data = load_data()

        # 추천 알고리즘 실행 (협업 필터링)
        recommended_titles = process_user_input(title, rating, review)

        # 중복값 제거
        recommended_titles = list(set(recommended_titles))

        top_reviews = []
        for title in recommended_titles:
            title_reviews = data[data['title2'] == title].sort_values(by='empathy', ascending=False).head(3)
            review_list = []
            for _, review in title_reviews.iterrows():
                review_list.append({
                    'title': review['title'],
                    'review': review['review'],
                    'empathy': int(review['empathy']),
                    'star': int(review['star']),
                    'url': review['url']
                })
            top_reviews.append({'title': title, 'reviews': review_list})

        # 추천 결과를 템플릿에 전달
        return render(request, 'analysis/analysis2.html', {
            'top_reviews': top_reviews,
            'recommended_titles': recommended_titles
        })
    # GET 요청일 경우, 입력 폼이 있는 페이지로 리다이렉트
    return render(request, 'home.html')

# views.py

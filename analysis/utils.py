import matplotlib
matplotlib.use('Agg')
import pandas as pd
import re
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from itertools import chain, combinations

# 키워드 그룹
keyword_groups = {
    "acting": ["배우", "캐스팅", "주연", "조연", "역할", "페어"],
    "performance": ["연기", "대사", "딕션", "소화력"],
    "music": ["음악", "노래", "넘버", "성량", "멜로디"],
    "production": ["연출", "무대", "앙상블", "춤", "오케스트라", "사운드", "연주", "음색", "의상", "장치"],
    "character": ["캐릭터", "인물", "해석"],
    "story": ["스토리", "이야기", "내용", "줄거리", "작품"],
}

actor_df = pd.read_csv('final_playlist.csv')

# Casting 컬럼의 모든 배우 이름을 리스트로 변환하여 'acting' 그룹에 추가
for casting in actor_df['Casting'].fillna(''):  # NaN 값을 빈 문자열로 대체
    # 문자열을 리스트로 변환 ('와 ,를 제거)
    actors = casting.replace("'", "").split(', ') if casting else []
    # 'acting' 그룹에 배우 이름 추가
    keyword_groups['acting'].extend(actors)
keyword_groups['acting'] = list(set(keyword_groups['acting']))  # 중복 제거

# def load_data():
#     reviews = Review.objects.filter(label=1)
#     data = pd.DataFrame(list(reviews.values()))
#     data = data.drop_duplicates(subset='review')
#     data = data[data['review'].str.len() >= 10]
#     return data

def load_data():
    # CSV 파일에서 데이터를 불러옵니다.
    data = pd.read_csv('review_data.csv')

    # 중복값 제거
    data = data.drop_duplicates(subset='review')

    # 리뷰 길이가 10자 이상인 것만 필터링
    data = data[data['review'].str.len() >= 10]
    
    return data

def preprocess_reviews(data):
    okt = Okt()

    def tokenize(text):
        return okt.morphs(text)

    data['tokens'] = data['review'].apply(tokenize)

    stopwords_df = pd.read_csv('stopword.csv', header=None)
    stopwords_list = stopwords_df[0].tolist()

    def remove_stopwords(tokens):
        return [token for token in tokens if token not in stopwords_list]

    data['tokens'] = data['tokens'].apply(remove_stopwords)

    def preprocess(text):
        text = re.sub(r'[^가-힣]', ' ', text)
        text = re.sub(r'\b\w{1}\b', '', text)
        return text

    def preprocess_tokens(tokens):
        text = ' '.join(tokens)
        processed_text = preprocess(text)
        processed_tokens = processed_text.split()
        return processed_tokens

    data['tokens'] = data['tokens'].apply(preprocess_tokens)
    return data

def calculate_tfidf(data):
    try:
        grouped = data.groupby('title2')['tokens'].apply(lambda tokens: ' '.join(chain.from_iterable(tokens))).reset_index()
        print("Grouped DataFrame created.")
        
        grouped['tokens'] = grouped['tokens'].str.replace(' ', '')
        grouped['tokens'] = grouped['tokens'].str.replace("','", ' ')
        grouped['tokens'] = grouped['tokens'].str.replace("['", ' ')
        grouped['tokens'] = grouped['tokens'].str.replace("']", ' ')
        grouped['tokens'] = grouped['tokens'].str.replace("']['", ' ')
        print("Token strings cleaned.")

        vocabulary = [word for group in keyword_groups.values() for word in group]

        tfidf_vectorizer = TfidfVectorizer(vocabulary=vocabulary, lowercase=False)
        tfidf_matrix = tfidf_vectorizer.fit_transform(grouped['tokens'])
        print("TF-IDF matrix calculated.")

        tfidf_scores = tfidf_matrix.toarray()

        group_tfidf_scores = defaultdict(dict)
        for i, title in enumerate(grouped['title2']):
            for group_name, keywords in keyword_groups.items():
                group_score = [tfidf_scores[i][tfidf_vectorizer.vocabulary_[keyword]] for keyword in keywords if keyword in tfidf_vectorizer.vocabulary_]
                group_tfidf_scores[title][group_name] = sum(group_score) / len(group_score) if group_score else 0

        group_tfidf_df = pd.DataFrame(group_tfidf_scores).T
        print("TF-IDF scores DataFrame created:", group_tfidf_df.head())
        
        scaler = StandardScaler()
        standardized_scores = scaler.fit_transform(group_tfidf_df)
        standardized_df = pd.DataFrame(standardized_scores, index=group_tfidf_df.index, columns=group_tfidf_df.columns)

        combinations_list = list(combinations(keyword_groups.keys(), 3))
        combination_scores = {}

        for comb in combinations_list:
            comb_name = '_'.join(comb)
            standardized_df[comb_name] = standardized_df[list(comb)].sum(axis=1)

        print("Final TF-IDF DataFrame columns:", standardized_df.columns.head())
        return standardized_df
    
    except Exception as e:
        print(f"An error occurred in calculate_tfidf: {e}")

import matplotlib
matplotlib.use('Agg')  # GUI 백엔드가 아닌 파일 백엔드를 사용하도록 설정
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

def generate_radar_chart(title, labels, values, color='blue', alpha=0.25):

    plt.rc('font', family='NanumGothic')  # 한글 폰트 설정
    num_vars = len(labels)

    # 각 축의 각도를 계산
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # 곡선을 닫기 위해 첫 번째 각도를 다시 추가

    values += values[:1]  # 값을 폐곡선으로 만들기 위해 첫 번째 값을 다시 추가

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    # 곡선과 채우기
    ax.plot(angles, values, color=color, linewidth=2, linestyle='solid')
    ax.fill(angles, values, color=color, alpha=alpha)

    # y축 단위 레이블 표시
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)

    # x축 라벨 표시
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=12, color='black')

    # labels와 values를 매칭하여 요약 텍스트 추가
    summary_text = "\n".join([f"{label}: {value}" for label, value in zip(labels, values[:-1])])

    # 요약 텍스트를 원 바깥에 배치
    fig.text(0.75, 0.95, summary_text, ha='left', fontsize=10,
             bbox=dict(facecolor='white', alpha=0.5), va='top')

    # # 제목 위치 조정
    # plt.title(title, size=20, color=color, y=1.1)
    # plt.subplots_adjust(top=0.85)

    # 이미지를 바이트 스트림으로 변환
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close(fig)

    return image_base64

def process_user_input(title, rating, review):
    # review_data.csv 파일 로드
    df = pd.read_csv('review_data.csv')  # 실제 경로로 수정 필요

    # stopword.csv 파일 로드
    stopwords_df = pd.read_csv('stopword.csv', header=None)
    stopwords_list = stopwords_df[0].tolist()  # 불용어 리스트 생성

    # 사용자가 입력한 데이터를 새로운 행으로 추가
    new_data = pd.DataFrame({'title2': [title], 'star': [rating], 'review': [review], 'empathy': [0], 'url': [''], 'label': [1]})
    df = pd.concat([df, new_data], ignore_index=True)

    # 리뷰 텍스트 벡터화 (TF-IDF) - 불용어 적용
    tfidf = TfidfVectorizer(stop_words=stopwords_list)
    tfidf_matrix = tfidf.fit_transform(df['review'])

    # 코사인 유사도를 계산하여 유사한 타이틀을 찾음
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # 입력된 title2의 인덱스를 가져옴
    idx = df[df['title2'] == title].index[-1]  # 사용자가 입력한 최신 데이터의 인덱스를 가져옴

    # 유사한 타이틀의 인덱스와 유사도를 정렬하여 상위 추천 타이틀을 선택
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # 가장 유사한 타이틀을 추출 (자기 자신을 제외) 및 입력된 타이틀과 일치하지 않는 타이틀만 포함
    recommended_titles = []
    for i in sim_scores:
        recommended_title = df['title2'].iloc[i[0]]
        if recommended_title != title:
            recommended_titles.append(recommended_title)
        if len(recommended_titles) >= 3:  # 상위 3개 추천
            break
    
    return recommended_titles
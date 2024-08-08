import pandas as pd
import re
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from collections import defaultdict
from itertools import chain, combinations
from analysis.models import Review

# 키워드 그룹
keyword_groups = {
    "acting": ["배우", "캐스팅", "주연", "조연", "역할", "페어"],
    "performance": ["연기", "대사", "딕션", "소화력"],
    "music": ["음악", "노래", "넘버", "성량", "멜로디"],
    "production": ["연출", "무대", "앙상블", "춤", "오케스트라", "사운드", "연주", "음색", "의상", "장치"],
    "character": ["캐릭터", "인물", "해석"],
    "story": ["스토리", "이야기", "내용", "줄거리", "작품"]
}

actor_df = pd.read_csv('final_playlist.csv')

# Casting 컬럼의 모든 배우 이름을 리스트로 변환하여 'acting' 그룹에 추가
for casting in actor_df['Casting'].fillna(''):  # NaN 값을 빈 문자열로 대체
    # 문자열을 리스트로 변환 ('와 ,를 제거)
    actors = casting.replace("'", "").split(', ') if casting else []
    # 'acting' 그룹에 배우 이름 추가
    keyword_groups['acting'].extend(actors)
keyword_groups['acting'] = list(set(keyword_groups['acting']))  # 중복 제거

def load_data():
    reviews = Review.objects.filter(label=1)
    data = pd.DataFrame(list(reviews.values()))
    data = data.drop_duplicates(subset='review')
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
    grouped = data.groupby('title2')['tokens'].apply(lambda tokens: ' '.join(chain.from_iterable(tokens))).reset_index()
    grouped['tokens'] = grouped['tokens'].str.replace(' ', '')
    grouped['tokens'] = grouped['tokens'].str.replace("','", ' ')
    grouped['tokens'] = grouped['tokens'].str.replace("['", ' ')
    grouped['tokens'] = grouped['tokens'].str.replace("']", ' ')
    grouped['tokens'] = grouped['tokens'].str.replace("']['", ' ')

    tfidf_vectorizer = TfidfVectorizer(vocabulary=[word for group in keyword_groups.values() for word in group])
    tfidf_matrix = tfidf_vectorizer.fit_transform(grouped['tokens'])
    tfidf_scores = tfidf_matrix.toarray()

    group_tfidf_scores = defaultdict(dict)
    for i, title in enumerate(grouped['title2']):
        for group_name, keywords in keyword_groups.items():
            group_score = [tfidf_scores[i][tfidf_vectorizer.vocabulary_[keyword]] for keyword in keywords if keyword in tfidf_vectorizer.vocabulary_]
            group_tfidf_scores[title][group_name] = sum(group_score) / len(group_score) if group_score else 0

    group_tfidf_df = pd.DataFrame(group_tfidf_scores).T
    scaler = StandardScaler()
    standardized_scores = scaler.fit_transform(group_tfidf_df)
    standardized_df = pd.DataFrame(standardized_scores, index=group_tfidf_df.index, columns=group_tfidf_df.columns)

    combinations_list = list(combinations(keyword_groups.keys(), 3))
    combination_scores = {}

    for comb in combinations_list:
        comb_name = '_'.join(comb)
        standardized_df[comb_name] = standardized_df[list(comb)].sum(axis=1)

    return standardized_df

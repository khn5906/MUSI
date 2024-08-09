import pandas as pd
from django.core.management.base import BaseCommand
from analysis.models import Review

class Command(BaseCommand):
    help = 'Load reviews from a CSV file'

    def handle(self, *args, **kwargs):
        data = pd.read_csv('review_data.csv')
        print(data.head())

        # 중복값 제거
        data = data.drop_duplicates(subset='review')

        for _, row in data.iterrows():
            # 기존에 동일한 리뷰가 있는지 확인
            if not Review.objects.filter(review=row['review']).exists():
                Review.objects.create(
                    title=row['title'],
                    star=row['star'],
                    review=row['review'],
                    empathy=row['empathy'],
                    title2=row['title2'],
                    url=row['url'],
                    label=row['label']
                )
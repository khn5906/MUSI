from django.db import models

# Create your models here.
class Review(models.Model):
    title = models.CharField(max_length=255)
    star = models.IntegerField()
    review = models.TextField()
    empathy = models.FloatField()
    title2 = models.CharField(max_length=255)
    url = models.URLField()
    label = models.IntegerField()

    def __str__(self):
        return self.title
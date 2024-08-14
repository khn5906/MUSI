
from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('analysis/', views.analysis, name='analysis'),  
    path('analysis_review/', views.analysis_review, name='review'),  
    path('process_input/', views.process_input, name='process_input'),     
    path('process_input/', views.process_input, name='process_input'),     
]

from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path("analysis/", views.analysis),  
    path("visualization/", views.visualization),    
]
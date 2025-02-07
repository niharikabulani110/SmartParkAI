from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_video, name='upload'),
    path('analyze/<path:video_path>/', views.analyze_video, name='analyze'),
]

from django.urls import path
from . import views

app_name = 'games'
urlpatterns = [
    path('', views.GameListView.as_view(), name='home'),
    path('game/<int:pk>/', views.GameDetailView.as_view(), name='detail'),
]
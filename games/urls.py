from django.urls import path
from . import views

app_name = 'games'
urlpatterns = [
    path('', views.GameListView.as_view(), name='home'),
    path('game/<int:pk>/', views.GameDetailView.as_view(), name='detail'),
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/signup/', views.SignUpView.as_view(), name='signup'),
]

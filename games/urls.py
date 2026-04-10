from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('', views.GameListView.as_view(), name='home'),
    path('game/<int:pk>/', views.GameDetailView.as_view(), name='detail'),
    path('signup/', views.SignUpView.as_view(), name='signup'),

    # Nuevas rutas de Perfil
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/delete/', views.DeleteAccountView.as_view(), name='delete_account'),
]
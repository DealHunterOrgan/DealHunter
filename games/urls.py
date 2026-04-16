from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'games'

urlpatterns = [
    path('', views.GameListView.as_view(), name='home'),
    path('game/<int:pk>/', views.GameDetailView.as_view(), name='detail'),
    path('wishlist/toggle/<int:pk>/', views.ToggleWishlistView.as_view(), name='toggle_wishlist'),
    path('review/add/<int:pk>/', views.AddReviewView.as_view(), name='add_review'),
    path('review/edit/<int:pk>/', views.EditReviewView.as_view(), name='edit_review'),
    path('review/delete/<int:pk>/', views.DeleteReviewView.as_view(), name='delete_review'),

    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.EditAccountView.as_view(), name='edit_account'),
    path('profile/delete/', views.DeleteAccountView.as_view(), name='delete_account'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='games:home'), name='logout'),
]
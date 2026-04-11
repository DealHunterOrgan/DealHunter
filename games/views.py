from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.views import View

from .forms import CustomUserCreationForm
from .models import Game, Wishlist, Genre, Platform

class GameListView(ListView):
    model = Game
    template_name = 'games/home.html'
    context_object_name = 'games'
    paginate_by = 12

    def get_queryset(self):
        qs = Game.objects.all().prefetch_related('platforms', 'availability_set', 'genres')
        q = self.request.GET.get('q', '').strip()
        genre = self.request.GET.get('genre')
        if q:
            qs = qs.filter(title__icontains=q)
        if genre:
            qs = qs.filter(genres__name=genre)
        return qs.order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['current_genre'] = self.request.GET.get('genre')
        context['all_genres'] = Genre.objects.all().order_by('name')
        return context

class GameDetailView(DetailView):
    model = Game
    template_name = 'games/detail.html'
    context_object_name = 'game'

    def get_queryset(self):
        return Game.objects.all().prefetch_related('platforms', 'genres', 'availability_set__shop')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_wishlisted'] = Wishlist.objects.filter(user=self.request.user, game=self.object).exists()
        else:
            context['is_wishlisted'] = False
        return context

# Vistas de Usuario y Autenticación
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('games:home')

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'

class DeleteAccountView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'registration/delete_confirm.html'
    success_url = reverse_lazy('games:home')

    def get_object(self, queryset=None):
        return self.request.user

class ToggleWishlistView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        wishlist_item = Wishlist.objects.filter(user=request.user, game=game).first()
        if wishlist_item:
            wishlist_item.delete()
        else:
            Wishlist.objects.create(user=request.user, game=game, desired_price=0.00)
        return redirect(request.META.get('HTTP_REFERER', 'games:home'))
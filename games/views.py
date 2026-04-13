from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy  # <--- IMPORTANTE PARA DELETEACCOUNT
from django.contrib.auth.models import User
from django.views import View
from django.http import HttpResponseForbidden

from .forms import CustomUserCreationForm
from .models import Game, Wishlist, Genre, Platform, Review

# --- VISTAS DE JUEGOS ---
class GameListView(ListView):
    model = Game
    template_name = 'games/home.html'
    context_object_name = 'games'
    paginate_by = 30

    def get_queryset(self):
        qs = Game.objects.all().prefetch_related('platforms', 'availability_set', 'genres')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(title__icontains=q)
        return qs.distinct().order_by('title')

class GameDetailView(DetailView):
    model = Game
    template_name = 'games/detail.html'
    context_object_name = 'game'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_wishlisted'] = Wishlist.objects.filter(
                user=self.request.user, game=self.object
            ).exists()
        else:
            context['is_wishlisted'] = False
        return context

# --- VISTAS DE USUARIO ---
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

# --- VISTAS DE WISHLIST ---
class ToggleWishlistView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        wishlist_item = Wishlist.objects.filter(user=request.user, game=game).first()
        if wishlist_item:
            wishlist_item.delete()
        else:
            Wishlist.objects.create(user=request.user, game=game, desired_price=0.00)
        return redirect('games:detail', pk=pk)

# --- VISTAS DE REVIEWS ---
class AddReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        content = request.POST.get('content', '').strip()
        if content:
            Review.objects.create(game=game, user=request.user, content=content)
        return redirect('games:detail', pk=pk)

class EditReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if review.user != request.user:
            return HttpResponseForbidden("No puedes editar esto.")
        new_content = request.POST.get('content', '').strip()
        if new_content:
            review.content = new_content
            review.save()
        return redirect('games:detail', pk=review.game.id)

class DeleteReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        if review.user != request.user:
            return HttpResponseForbidden("No puedes borrar esto.")
        game_id = review.game.id
        review.delete()
        return redirect('games:detail', pk=game_id)
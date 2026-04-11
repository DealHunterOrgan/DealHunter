from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.views.generic import ListView, DetailView, CreateView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.views import View
from django.shortcuts import get_object_or_404, redirect

from .forms import CustomUserCreationForm
from .models import Game, Wishlist

# ... (Tus vistas GameListView, GameDetailView, CustomLoginView y SignUpView se mantienen igual) ...

class GameListView(ListView):
    model = Game
    template_name = 'games/home.html'
    context_object_name = 'games'
    paginate_by = 40

    def get_queryset(self):
        queryset = Game.objects.all().prefetch_related('platforms', 'availability_set').order_by('title')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(title__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        return context

class GameDetailView(DetailView):
    model = Game
    template_name = 'games/detail.html'
    context_object_name = 'game'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_wishlisted'] = Wishlist.objects.filter(user=self.request.user, game=self.object).exists()
        else:
            context['is_wishlisted'] = False
        return context

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('games:home')

# --- NUEVAS VISTAS ---

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = ""
        return context

class DeleteAccountView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'registration/delete_confirm.html'
    success_url = reverse_lazy('games:home')

    def get_object(self, queryset=None):
        return self.request.user

# Wishlist view (login required))
class ToggleWishlistView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)

        # Busquem si l'usuari ja té aquest joc a la taula Wishlist
        wishlist_item = Wishlist.objects.filter(user=request.user, game=game).first()

        if wishlist_item:
            # Si ja el té, l'esborrem de la taula
            wishlist_item.delete()
        else:
            # Si no el té, creem el registre (posem desired_price a 0)
            Wishlist.objects.create(user=request.user, game=game, desired_price=0.00)

        return redirect(request.META.get('HTTP_REFERER', 'games:home'))
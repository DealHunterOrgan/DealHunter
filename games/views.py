from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.views import View

from .forms import CustomUserCreationForm
from .models import Game, Wishlist, Genre


class GameListView(ListView):
    model = Game
    template_name = 'games/home.html'
    context_object_name = 'games'
    paginate_by = 12

    def get_queryset(self):
        # Optimitzem la consulta amb prefetch_related incloent genres
        queryset = (
            Game.objects.all()
            .prefetch_related('platforms', 'availability_set', 'genres')
            .order_by('title')
        )

        # Filtre de cerca per text (Buscador)
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(title__icontains=query)

        # Filtre per Gènere (Barra lateral)
        genre_name = self.request.GET.get('genre')
        if genre_name:
            queryset = queryset.filter(genres__name=genre_name)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mantenim els valors actuals per a la cerca i el filtre a la plantilla
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['current_genre'] = self.request.GET.get('genre')

        # Enviem tots els gèneres disponibles a la barra lateral
        context['all_genres'] = Genre.objects.all().order_by('name')
        return context


class GameDetailView(DetailView):
    model = Game
    template_name = 'games/detail.html'
    context_object_name = 'game'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Comprovem si el joc està a la Wishlist de l'usuari
        if self.request.user.is_authenticated:
            context['is_wishlisted'] = Wishlist.objects.filter(
                user=self.request.user,
                game=self.object
            ).exists()
        else:
            context['is_wishlisted'] = False
        return context


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = ""
        return context


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('games:home')


# --- VISTES DE PERFIL I COMPTE ---

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
        # Assegurem que l'usuari només pugui esborrar el seu propi compte
        return self.request.user


# --- VISTES DE WISHLIST ---

class ToggleWishlistView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)

        # Busquem si l'usuari ja té aquest joc a la taula Wishlist
        wishlist_item = Wishlist.objects.filter(user=request.user, game=game).first()

        if wishlist_item:
            # Si ja el té, l'esborrem de la taula
            wishlist_item.delete()
        else:
            # Si no el té, creem el registre (posem desired_price a 0.00 per defecte)
            Wishlist.objects.create(user=request.user, game=game, desired_price=0.00)

        # Redirigim a la pàgina d'on venia l'usuari
        return redirect(request.META.get('HTTP_REFERER', 'games:home'))